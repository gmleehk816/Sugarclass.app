"""
AI Tutor Main Application

FastAPI application for the AI Tutor system.
Initializes all components and provides the API endpoints.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from pathlib import Path
import httpx

from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global instances
_content_db_builder = None
_agent_db_manager = None
_vector_store_sync = None
_tutor_workflow = None
_llm = None
_embedding_model = None
_sync_manager = None


async def init_databases():
    """Initialize database connections."""
    global _content_db_builder, _agent_db_manager

    from .database import ContentDatabaseBuilder, AgentDBManager

    content_db_url = os.getenv(
        "CONTENT_DB_URL",
        "postgresql://tutor:tutor_content_pass@localhost:5433/tutor_content"
    )
    agent_db_url = os.getenv(
        "AGENT_DB_URL",
        "postgresql://tutor:tutor_agent_pass@localhost:5434/tutor_agent"
    )

    # Initialize content database builder
    content_source = os.getenv(
        "CONTENT_SOURCE_PATH",
        "C:/Users/gmhome/SynologyDrive/coding/tutorrag/database"
    )
    _content_db_builder = ContentDatabaseBuilder(
        content_root=content_source,
        database_url=content_db_url
    )
    await _content_db_builder.connect()
    logger.info("Content database connected")

    # Initialize agent database manager
    _agent_db_manager = AgentDBManager(database_url=agent_db_url)
    await _agent_db_manager.connect()
    logger.info("Agent database connected")


async def init_vector_store():
    """Initialize vector store and sync."""
    global _vector_store_sync, _embedding_model

    from .database import VectorStoreSync

    # Initialize embedding model
    embedding_model_name = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
    embedding_dim = int(os.getenv("EMBEDDING_DIM", "384"))

    try:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer(embedding_model_name)
        logger.info(f"Loaded embedding model: {embedding_model_name}")
    except ImportError:
        logger.warning("sentence-transformers not installed, using None for embeddings")
        _embedding_model = None

    # Initialize vector store sync
    content_db_url = os.getenv(
        "CONTENT_DB_URL",
        "postgresql://tutor:tutor_content_pass@localhost:5433/tutor_content"
    )
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    collection_name = os.getenv("QDRANT_COLLECTION", "aitutor_documents")

    _vector_store_sync = VectorStoreSync(
        content_db_url=content_db_url,
        qdrant_url=qdrant_url,
        collection_name=collection_name,
        embedding_model=_embedding_model,
        embedding_dim=embedding_dim
    )
    await _vector_store_sync.connect()
    logger.info("Vector store connected")


async def init_llm():
    """Initialize the language model."""
    global _llm

    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    llm_model = os.getenv("LLM_MODEL", "gpt-4o-mini")

    try:
        if llm_provider == "google_genai":
            # Google GenAI (Gemini)
            from langchain_google_genai import ChatGoogleGenerativeAI
            api_key = os.getenv("GOOGLE_API_KEY")
            _llm = ChatGoogleGenerativeAI(
                model=llm_model,
                temperature=0.7,
                api_key=api_key,
                timeout=60,
                request_timeout=60
            )
            logger.info(f"Initialized Google GenAI LLM: {llm_model}")

        elif llm_provider == "openai_compatible":
            # OpenAI-compatible endpoint (e.g., Gemini, local LLMs)
            from langchain_openai import ChatOpenAI
            api_base = os.getenv("LLM_API_BASE")
            api_key = os.getenv("LLM_API_KEY")
            _llm = ChatOpenAI(
                model=llm_model,
                temperature=0.7,
                openai_api_key=api_key,
                openai_api_base=api_base,
                timeout=60,
                request_timeout=60
            )
            logger.info(f"Initialized OpenAI-compatible LLM: {llm_model} at {api_base}")

        elif llm_provider == "openai":
            from langchain_openai import ChatOpenAI
            _llm = ChatOpenAI(
                model=llm_model,
                temperature=0.7,
                api_key=os.getenv("OPENAI_API_KEY"),
                timeout=60,
                request_timeout=60
            )
            logger.info(f"Initialized OpenAI LLM: {llm_model}")

        elif llm_provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            _llm = ChatAnthropic(
                model=llm_model,
                temperature=0.7,
                api_key=os.getenv("ANTHROPIC_API_KEY")
            )
            logger.info(f"Initialized Anthropic LLM: {llm_model}")

        else:
            logger.warning(f"Unknown LLM provider: {llm_provider}")
            _llm = None

    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        _llm = None

async def init_workflow():
    """Initialize tutor workflow."""
    global _tutor_workflow

    from .agents import TutorWorkflow
    from .agents.tools import (
        init_sql_retriever,
        init_profile_manager,
        init_quiz_generator,
        init_rag_retriever,
        init_chapter_list_retriever,
        postgres_retriever_tool,
        profile_manager_tool,
        quiz_generator_tool,
        rag_retriever_tool,
        chapter_list_tool
    )

    # Initialize tools - now using PostgreSQL as primary
    if _content_db_builder and _content_db_builder.pool:
        init_sql_retriever(_content_db_builder.pool)
        logger.info("PostgreSQL SQL retriever initialized")
        
        # Initialize PostgreSQL retriever (NEW)
        # init_postgres_retriever(_content_db_builder.pool)
        # logger.info("PostgreSQL content retriever initialized")

    if _agent_db_manager:
        init_profile_manager(_agent_db_manager)
        logger.info("Profile manager initialized")

    if _llm and _content_db_builder:
        init_quiz_generator(_llm, _content_db_builder.pool)
        logger.info("Quiz generator initialized")

    if _vector_store_sync and _embedding_model:
        init_rag_retriever(
            _vector_store_sync.qdrant_client,
            _embedding_model,
            os.getenv("QDRANT_COLLECTION", "aitutor_documents")
        )
        logger.info("RAG retriever initialized")
        
        init_chapter_list_retriever(
            _vector_store_sync.qdrant_client,
            _embedding_model,
            os.getenv("QDRANT_COLLECTION", "aitutor_documents")
        )
        logger.info("Chapter list retriever initialized")

    # Create workflow with tools - now PostgreSQL-focused
    tools = {}
    # if postgres_retriever_tool:
    #     tools["postgres_retriever"] = postgres_retriever_tool
    #     logger.info("PostgreSQL retriever added to workflow")
    # if sql_retriever_tool:
    #     tools["sqlite_retriever"] = sql_retriever_tool
    if profile_manager_tool:
        tools["profile_manager"] = profile_manager_tool
    if quiz_generator_tool:
        tools["quiz_generator"] = quiz_generator_tool
    if rag_retriever_tool:
        tools["rag_retriever"] = rag_retriever_tool
    if chapter_list_tool:
        tools["chapter_list_retriever"] = chapter_list_tool
        logger.info("Chapter list retriever added to workflow")

    _tutor_workflow = TutorWorkflow(llm=_llm, tools=tools)
    logger.info("Tutor workflow initialized")


async def init_api_router(app: FastAPI):
    """Initialize and register API router."""
    from .api import tutor_router, init_tutor_router

    # Initialize router with service instances
    init_tutor_router(
        tutor_service=_tutor_workflow,
        db_manager=_agent_db_manager,
        content_db=_content_db_builder
    )

    # Include router
    app.include_router(tutor_router)
    logger.info("API router registered")


async def init_sync_manager():
    """Initialize sync manager for database-Qdrant sync tracking."""
    global _sync_manager
    
    from .sync.sync_manager import SyncManager
    
    materials_path = os.getenv("CONTENT_SOURCE_PATH", "/app/materials")
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    collection_name = os.getenv("QDRANT_COLLECTION", "aitutor_documents")
    content_db_url = os.getenv(
        "CONTENT_DB_URL",
        "postgresql://tutor:tutor_content_pass@localhost:5433/tutor_content"
    )
    
    _sync_manager = SyncManager(
        db_url=content_db_url,
        qdrant_url=qdrant_url,
        qdrant_collection=collection_name,
        materials_path=materials_path
    )
    logger.info("Sync manager initialized")


async def close_connections():
    """Close all database connections."""
    if _content_db_builder:
        await _content_db_builder.close()
    if _agent_db_manager:
        await _agent_db_manager.close()
    if _vector_store_sync:
        await _vector_store_sync.close()
    if _sync_manager:
        _sync_manager.close()
    logger.info("All connections closed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting AI Tutor service...")

    try:
        # Initialize components
        await init_databases()
        await init_vector_store()
        await init_llm()
        await init_workflow()
        await init_api_router(app)
        await init_sync_manager()

        logger.info("AI Tutor service started successfully")
        yield

    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise

    finally:
        logger.info("Shutting down AI Tutor service...")
        await close_connections()
        logger.info("AI Tutor service stopped")


# Create FastAPI application
app = FastAPI(
    title="AI Tutor Service",
    description="Intelligent tutoring system with LangGraph agents",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# RAG Service URL for proxying
RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:8002")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "AI Tutor",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "components": {
            "content_db": _content_db_builder is not None,
            "agent_db": _agent_db_manager is not None,
            "vector_store": _vector_store_sync is not None,
            "llm": _llm is not None,
            "workflow": _tutor_workflow is not None,
            "sync_manager": _sync_manager is not None
        }
    }


@app.get("/api/health")
async def api_health():
    """Check the health of the RAG service for frontend compatibility."""
    return {
        "status": "healthy",
        "rag_service": True
    }


# ==================== RAG Proxy Endpoints ====================
# These endpoints proxy requests to the main RAG service (port 8002)

@app.post("/query")
async def query_rag_system(
    question: str = Body(..., embed=True),
    use_graph: bool = False,
    context: Optional[Dict[str, Any]] = None
):
    """
    Sends a natural language query to the RAG system.
    """
    if not _tutor_workflow:
        raise HTTPException(status_code=503, detail="Tutor workflow not initialized.")
    
    try:
        logger.info(f"Received direct query: {question}")
        
        # Use the rag_retriever tool directly
        from .agents.tools import rag_retriever_tool
        
        # Get context from request
        syllabus = context.get("syllabus") if context else None
        subject = context.get("subject") if context else None
        
        # Retrieve documents
        sources = await rag_retriever_tool.ainvoke({
            "query": question,
            "syllabus": syllabus,
            "subject": subject,
            "limit": 5
        })
        
        # Generate answer using LLM
        if _llm:
            prompt = f"""You are a helpful AI Tutor. Use the following pieces of retrieved context to answer the question. 
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            
            Context: {sources}
            
            Question: {question}
            
            Answer:"""
            
            response = await _llm.ainvoke(prompt)
            answer = response.content
        else:
            answer = "LLM not initialized. Here are the retrieved sources: " + str(sources)

        return {
            "answer": answer,
            "sources": sources,
            "success": True
        }
    except Exception as e:
        logger.error(f"Error in direct query: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query")
async def proxy_rag_query(
    request: Request,
    use_graph: bool = False
):
    """
    Proxy RAG query requests locally to the /query endpoint.
    """
    try:
        body = await request.json()
        question = body.get("question", "")
        context = body.get("context", {})
        
        # Call the local query function directly instead of HTTP proxy
        return await query_rag_system(question=question, use_graph=use_graph, context=context)
                
    except Exception as e:
        logger.error(f"Error in proxy RAG query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/topics/subject/{subject_name}")
async def proxy_rag_topics(subject_name: str):
    """
    Get topics for a specific subject from the RAG service.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{RAG_SERVICE_URL}/topics/subject/{subject_name}",
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"RAG service error: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="RAG service timeout")
    except Exception as e:
        logger.error(f"Error proxying topics request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/materials/subject/{subject_name}/content")
async def proxy_rag_content(subject_name: str, topic_name: Optional[str] = None):
    """
    Get content for a specific subject from the RAG service.
    """
    try:
        url = f"{RAG_SERVICE_URL}/materials/subject/{subject_name}/content"
        if topic_name:
            url += f"?topic_name={topic_name}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"RAG service error: {response.text}"
                )
                
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="RAG service timeout")
    except Exception as e:
        logger.error(f"Error proxying content request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Sync endpoints
@app.get("/sync/status")
async def get_sync_status():
    """
    Get current sync status between database and Qdrant.
    Shows if database tracking is in sync with actual Qdrant collection.
    """
    if not _sync_manager:
        raise HTTPException(status_code=503, detail="Sync manager not initialized.")
    
    try:
        status = _sync_manager.get_sync_status()
        return status
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sync/files/check")
async def check_files_sync(file_paths: Optional[str] = None):
    """
    Check sync status for files.
    
    Query params:
    - file_paths: Optional comma-separated list of specific files to check. If not provided, scans all files.
    
    Returns:
    - List of synced, modified, new, and missing files
    """
    if not _sync_manager:
        raise HTTPException(status_code=503, detail="Sync manager not initialized.")
    
    try:
        paths_to_check = None
        if file_paths:
            paths_to_check = [fp.strip() for fp in file_paths.split(',')]
        
        result = _sync_manager.check_files_sync(paths_to_check)
        return result
    except Exception as e:
        logger.error(f"Error checking files sync: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sync/events")
async def get_sync_events(
    limit: int = 50,
    event_type: Optional[str] = None,
    file_path: Optional[str] = None
):
    """
    Get sync events from the database.
    
    Query params:
    - limit: Maximum number of events to return (default: 50)
    - event_type: Filter by event type (e.g., 'ingest', 'update', 'delete', 'sync_check')
    - file_path: Filter by file path
    """
    if not _sync_manager:
        raise HTTPException(status_code=503, detail="Sync manager not initialized.")
    
    try:
        events = _sync_manager.get_sync_events(
            limit=limit,
            event_type=event_type,
            file_path=file_path
        )
        return {
            "events": events,
            "count": len(events)
        }
    except Exception as e:
        logger.error(f"Error getting sync events: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sync/qdrant/update")
async def update_qdrant_status():
    """
    Update Qdrant collection status in database.
    This should be called after any manual ingestion to keep tracking up to date.
    """
    if not _sync_manager:
        raise HTTPException(status_code=503, detail="Sync manager not initialized.")
    
    try:
        _sync_manager.update_qdrant_status()
        return {
            "status": "success",
            "message": "Qdrant collection status updated in database"
        }
    except Exception as e:
        logger.error(f"Error updating Qdrant status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "services.rag_service.tutor_main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("DEBUG", "false").lower() == "true"
    )
