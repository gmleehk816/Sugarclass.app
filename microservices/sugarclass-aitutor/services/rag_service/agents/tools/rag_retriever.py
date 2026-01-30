"""
RAG Retriever Tool for AI Tutor

LangChain tool for semantic search using the Qdrant vector store.
Retrieves relevant content based on query similarity.
"""

import logging
from typing import Dict, Any, Optional, List

try:
    from langchain_core.tools import tool, BaseTool
    from pydantic import BaseModel, Field
except ImportError:
    tool = None
    BaseTool = object
    BaseModel = object
    Field = lambda **kwargs: None

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue
except ImportError:
    QdrantClient = None
    Filter = None

logger = logging.getLogger(__name__)


class RAGRetrieverInput(BaseModel):
    """Input schema for RAG retriever tool."""
    query: str = Field(
        description="The search query to find relevant content"
    )
    syllabus: Optional[str] = Field(
        default=None,
        description="Filter by syllabus/curriculum (e.g., 'CIE_IGCSE')"
    )
    subject: Optional[str] = Field(
        default=None,
        description="Filter by subject (e.g., 'Mathematics')"
    )
    chapter: Optional[str] = Field(
        default=None,
        description="Filter by chapter (e.g., 'Differentiation')"
    )
    content_type: Optional[str] = Field(
        default=None,
        description="Filter by content type: 'textbook', 'exercise', 'exam_qa'"
    )
    difficulty_level: Optional[str] = Field(
        default=None,
        description="Filter by difficulty: 'foundation', 'core', 'extended'"
    )
    limit: int = Field(
        default=5,
        description="Maximum number of results to return"
    )


class RAGRetrieverTool(BaseTool):
    """
    Tool for semantic search over educational content.

    Uses Qdrant vector store to find content similar to the query,
    with optional filtering by syllabus, subject, and content type.
    """

    name: str = "rag_retriever"
    description: str = """Search for relevant educational content using semantic similarity.
    Use this to find content related to a student's question or topic.
    Returns ranked results with content previews and metadata."""

    args_schema: type = RAGRetrieverInput

    qdrant_client: Any = None
    embedding_model: Any = None
    collection_name: str = "aitutor_documents"

    def __init__(
        self,
        qdrant_client: Any = None,
        embedding_model: Any = None,
        collection_name: str = "aitutor_documents",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.qdrant_client = qdrant_client
        self.embedding_model = embedding_model
        self.collection_name = collection_name

    def _run(self, **kwargs) -> List[Dict[str, Any]]:
        """Synchronous run."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(self._arun(**kwargs))

    async def _arun(
        self,
        query: str,
        syllabus: Optional[str] = None,
        subject: Optional[str] = None,
        chapter: Optional[str] = None,
        content_type: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Async semantic search over vector store."""
        if self.qdrant_client is None:
            logger.error("Qdrant client not initialized")
            return []

        if self.embedding_model is None:
            logger.error("Embedding model not initialized")
            return []

        try:
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            if query_embedding is None:
                logger.error(f"Failed to generate embedding for query: {query[:50]}")
                return []

            logger.debug(f"Generated embedding with {len(query_embedding)} dimensions for: {query[:50]}")

            # NEW: If subject is None, get MORE results to enable better subject switching
            if subject is None:
                limit = max(limit * 2, 10)  # Get more results for better subject diversity
                logger.info(f"No subject filter, increasing limit to {limit} for subject switching")

            # Build filter conditions
            filter_conditions = []

            if syllabus:
                filter_conditions.append(
                    FieldCondition(
                        key="syllabus",
                        match=MatchValue(value=syllabus)
                    )
                )

            if subject:
                filter_conditions.append(
                    FieldCondition(
                        key="subject",
                        match=MatchValue(value=subject)
                    )
                )

            if chapter:
                filter_conditions.append(
                    FieldCondition(
                        key="chapter",
                        match=MatchValue(value=chapter)
                    )
                )

            if content_type:
                filter_conditions.append(
                    FieldCondition(
                        key="content_type",
                        match=MatchValue(value=content_type)
                    )
                )

            if difficulty_level:
                filter_conditions.append(
                    FieldCondition(
                        key="difficulty_level",
                        match=MatchValue(value=difficulty_level)
                    )
                )
            
            # Create filter if conditions exist
            search_filter = None
            if filter_conditions and Filter is not None:
                search_filter = Filter(must=filter_conditions)

            # Perform search - handle different Qdrant client versions
            results = []
            try:
                # Try the newer 'search' method first (Qdrant >= 1.7.0)
                results = self.qdrant_client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=limit,
                    query_filter=search_filter
                )
                logger.debug(f"search() returned {len(results) if results else 0} results")
            except AttributeError as e:
                logger.debug(f"search() not available: {e}, trying query_points()")
                # Fallback to older 'query_points' method (Qdrant < 1.7.0)
                try:
                    query_response = self.qdrant_client.query_points(
                        collection_name=self.collection_name,
                        query=query_embedding,
                        limit=limit,
                        query_filter=search_filter
                    )
                    # QueryResponse has a .points attribute containing the actual results
                    results = query_response.points if hasattr(query_response, 'points') else []
                    logger.debug(f"query_points() returned {len(results) if results else 0} results")
                except AttributeError as e2:
                    logger.debug(f"query_points() not available: {e2}, trying search(vector=)")
                    # Last resort - try 'search' with 'query_vector' as 'vector'
                    results = self.qdrant_client.search(
                        collection_name=self.collection_name,
                        vector=query_embedding,
                        limit=limit,
                        query_filter=search_filter
                    )
                    logger.debug(f"search(vector=) returned {len(results) if results else 0} results")

            # Format results - handle different Qdrant return formats
            formatted_results = []
            for hit in results:
                try:
                    # Handle tuple format (score, point) or object format
                    if isinstance(hit, tuple):
                        score = hit[0]
                        point = hit[1] if len(hit) > 1 else None
                        payload = point.payload if point and hasattr(point, 'payload') else {}
                    else:
                        score = getattr(hit, 'score', 0.0)
                        payload = getattr(hit, 'payload', {})

                    formatted_results.append({
                        "score": score,
                        "syllabus_id": payload.get("syllabus_id"),
                        "syllabus": payload.get("syllabus"),
                        "subject": payload.get("subject"),
                        "chapter": payload.get("chapter"),
                        "subtopic": payload.get("subtopic"),
                        "content_type": payload.get("content_type"),
                        "difficulty_level": payload.get("difficulty_level"),
                        "chunk_type": payload.get("chunk_type"),
                        "content_preview": payload.get("content", "")[:500]
                    })
                except Exception as format_error:
                    logger.warning(f"Error formatting hit: {format_error}")
                    continue

            # NEW: Check if results are from multiple subjects
            subjects_found = set()
            for result in formatted_results:
                subj = result.get('subject')
                if subj:
                    subjects_found.add(subj)
            
            if subjects_found:
                logger.info(f"RAG found content from {len(subjects_found)} subjects: {list(subjects_found)}")
            
            logger.info(f"RAG retriever found {len(formatted_results)} results for: {query[:50]}...")
            return formatted_results

        except Exception as e:
            logger.error(f"RAG retrieval error: {e}")
            return []

    def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text."""
        if self.embedding_model is None:
            return None

        try:
            # Handle different embedding model interfaces
            if hasattr(self.embedding_model, 'embed_query'):
                return self.embedding_model.embed_query(text)
            elif hasattr(self.embedding_model, 'encode'):
                result = self.embedding_model.encode(text)
                return result.tolist() if hasattr(result, 'tolist') else list(result)
            elif callable(self.embedding_model):
                return self.embedding_model(text)
            else:
                logger.warning("Unknown embedding model interface")
                return None
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return None


# Global instance for functional tool
_rag_retriever_instance: Optional[RAGRetrieverTool] = None


def init_rag_retriever(
    qdrant_client: Any,
    embedding_model: Any,
    collection_name: str = "aitutor_documents"
) -> None:
    """Initialize the RAG retriever with Qdrant client and embedding model."""
    global _rag_retriever_instance
    _rag_retriever_instance = RAGRetrieverTool(
        qdrant_client=qdrant_client,
        embedding_model=embedding_model,
        collection_name=collection_name
    )


if tool is not None:
    @tool
    async def rag_retriever_tool(
        query: str,
        syllabus: Optional[str] = None,
        subject: Optional[str] = None,
        chapter: Optional[str] = None,
        content_type: Optional[str] = None,
        difficulty_level: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant educational content using semantic similarity.

        Use this to find content related to a student's question or topic.
        The search uses vector embeddings to find semantically similar content.

        Args:
            query: Query (student's question or topic)
            syllabus: Filter by curriculum (e.g., 'CIE_IGCSE', 'IB')
            subject: Filter by subject (e.g., 'Mathematics', 'Physics')
            content_type: Filter by type ('textbook', 'exercise', 'exam_qa')
            difficulty_level: Filter by difficulty ('foundation', 'core', 'extended')
            limit: Maximum results to return (default 5)

        Returns:
            List of relevant content with scores and metadata
        """
        if _rag_retriever_instance is None:
            logger.warning("RAG retriever not initialized")
            return []

        return await _rag_retriever_instance._arun(
            query=query,
            syllabus=syllabus,
            subject=subject,
            chapter=chapter,
            content_type=content_type,
            difficulty_level=difficulty_level,
            limit=limit
        )
else:
    rag_retriever_tool = None
