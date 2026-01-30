"""
Tutor API Endpoints

FastAPI router for the AI Tutor system.
Provides endpoints for sessions, chat, and student management.
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tutor", tags=["tutor"])


# ==================== Request/Response Models ====================

class StartSessionRequest(BaseModel):
    """Request to start a new tutoring session."""
    user_id: str = Field(..., description="External user identifier")
    name: Optional[str] = Field(None, description="Student name")
    grade_level: Optional[str] = Field(None, description="Grade level")
    curriculum: Optional[str] = Field(None, description="Curriculum/syllabus")
    subject: Optional[str] = Field(None, description="Subject to study")
    topic: Optional[str] = Field(None, description="Specific topic")


class StartSessionResponse(BaseModel):
    """Response after starting a session."""
    session_id: str
    student_id: int
    message: str
    created_at: datetime


class ChatRequest(BaseModel):
    """Request for chat interaction."""
    session_id: str = Field(..., description="Session identifier")
    message: str = Field(..., description="User message")


class ChatResponse(BaseModel):
    """Response from chat interaction."""
    session_id: str
    response: str
    response_type: str = "text"
    intent: Optional[str] = None
    quiz_active: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EndSessionRequest(BaseModel):
    """Request to end a session."""
    session_id: str


class StudentProfileResponse(BaseModel):
    """Student profile information."""
    student_id: int
    user_id: str
    name: Optional[str]
    grade_level: Optional[str]
    curriculum: Optional[str]
    mastery_summary: Dict[str, Any] = Field(default_factory=dict)
    statistics: Dict[str, Any] = Field(default_factory=dict)


class MasteryUpdateRequest(BaseModel):
    """Request to manually update mastery."""
    student_id: int
    syllabus_id: int
    subject: str
    chapter: str
    subtopic: str
    is_correct: bool
    score: Optional[float] = None


class ContentSearchRequest(BaseModel):
    """Request to search content."""
    query: str
    syllabus: Optional[str] = None
    subject: Optional[str] = None
    content_type: Optional[str] = None
    limit: int = 10


# ==================== Dependency Injection ====================

# These will be set during app initialization
_tutor_service = None
_db_manager = None
_content_db = None


def get_tutor_service():
    """Get the tutor service instance."""
    if _tutor_service is None:
        raise HTTPException(status_code=503, detail="Tutor service not initialized")
    return _tutor_service


def get_db_manager():
    """Get the database manager instance."""
    if _db_manager is None:
        raise HTTPException(status_code=503, detail="Database not initialized")
    return _db_manager


def get_content_db():
    """Get the content database instance."""
    if _content_db is None:
        raise HTTPException(status_code=503, detail="Content database not initialized")
    return _content_db


def init_tutor_router(tutor_service, db_manager, content_db):
    """Initialize the router with service instances."""
    global _tutor_service, _db_manager, _content_db
    _tutor_service = tutor_service
    _db_manager = db_manager
    _content_db = content_db
    logger.info("Tutor router initialized")


# ==================== Session Endpoints ====================

@router.post("/session/start", response_model=StartSessionResponse)
async def start_session(
    request: StartSessionRequest,
    db_manager = Depends(get_db_manager)
):
    """
    Start a new tutoring session.

    Creates or retrieves student profile and initializes a new session.
    """
    try:
        from ..database.agent_db_manager import StudentProfile, SessionData

        # Create or get student
        profile = StudentProfile(
            user_id=request.user_id,
            name=request.name,
            grade_level=request.grade_level,
            curriculum=request.curriculum
        )
        student_id = await db_manager.create_student(profile)

        # Create session
        session_id = str(uuid.uuid4())
        session = SessionData(
            session_id=session_id,
            student_id=student_id,
            subject=request.subject,
            current_topic=request.topic
        )
        await db_manager.create_session(session)

        logger.info(f"Started session {session_id} for student {student_id}, subject={request.subject}, curriculum={request.curriculum}")

        # Create welcome message without f-string backslash issue
        if request.subject:
            welcome_msg = f"Welcome! I'm your AI tutor. Let's study {request.subject}!"
        else:
            welcome_msg = "Welcome! I'm your AI tutor. What would you like to learn today?"
        
        return StartSessionResponse(
            session_id=session_id,
            student_id=student_id,
            message=welcome_msg,
            created_at=datetime.now()
        )

    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/end")
async def end_session(
    request: EndSessionRequest,
    db_manager = Depends(get_db_manager)
):
    """End a tutoring session."""
    try:
        success = await db_manager.end_session(request.session_id)
        if success:
            return {"status": "success", "message": "Session ended"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ending session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/session/{session_id}")
async def get_session(
    session_id: str,
    db_manager = Depends(get_db_manager)
):
    """Get session information."""
    try:
        session = await db_manager.get_session(session_id)
        if session:
            return session
        raise HTTPException(status_code=404, detail="Session not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Chat Endpoints ====================

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    tutor_service = Depends(get_tutor_service),
    db_manager = Depends(get_db_manager)
):
    """
    Send a message and get a response from the AI tutor (non-streaming).

    The tutor will:
    - Classify intent (learn, practice, review, question)
    - Retrieve relevant content
    - Generate an appropriate response
    - Track mastery if answering quiz questions
    """
    try:
        # Get session
        session = await db_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Increment message count
        await db_manager.increment_session_messages(request.session_id)

        # Get student info
        student = await db_manager.get_student_by_id(session["student_id"])

        # Run the tutor workflow
        # DON'T create a fresh state - let checkpointer load it!
        # Creating a fresh state overwrites the checkpointer's saved state
        from ..agents.state import create_initial_state, ContentContext, StudentContext

        # Try to get existing state from checkpointer
        # This is handled by passing session_id as thread_id in config
        # The workflow will load the saved state automatically

        # CRITICAL: Create proper Pydantic objects instead of partial dicts
        # LangGraph doesn't properly merge nested dicts into Pydantic models
        # This was causing subject to be lost (always None) even when session had a subject
        session_subject = session.get("subject")
        session_topic = session.get("current_topic")

        logger.info(f"Chat request - session subject: {session_subject}, topic: {session_topic}")
        logger.info(f"Chat request - session data: {session}")

        state_dict = {
            "session_id": request.session_id,
            "user_input": request.message,
            "student": StudentContext(
                student_id=session["student_id"],
                user_id=student["user_id"] if student else "unknown",
                name=student.get("name") if student else None,
                grade_level=student.get("grade_level") if student else None,
                curriculum=student.get("curriculum") if student else None
            ).model_dump(),
            "content": ContentContext(
                subject=session_subject,  # Pass subject to RAG for filtering
                subtopic=session_topic
            ).model_dump()
        }
        
        # CRITICAL: Pass subject from session to override any cached state
        # Our new state reducers will ensure this subject is merged correctly
        content_dict = state_dict['content']
        logger.info(f"Chat request - state_dict.content.subject: {content_dict.get('subject')}")

        # Run workflow - now safely using checkpointer with reducers
        result_state = await tutor_service.run(
            state_dict, 
            config={}  # Thread ID will be automatically added from session_id
        )

        # Update session with detected subject and topic to maintain context
        try:
            # ContentContext is a Pydantic model, not a dict
            if hasattr(result_state, 'content'):
                content = result_state.content
                subject = getattr(content, 'subject', None)
                subtopic = getattr(content, 'subtopic', None)
                
                if subject or subtopic:
                    session_updates = {}
                    if subject:
                        session_updates["subject"] = subject
                    if subtopic:
                        session_updates["current_topic"] = subtopic
                    
                    if session_updates:
                        await db_manager.update_session(request.session_id, session_updates)
        except Exception as e:
            logger.error(f"Error updating session: {e}")
            # Don't fail the request if session update fails

        # Prepare sources from RAG results
        sources = result_state.content.rag_results if result_state.content.rag_results else []
        
        return ChatResponse(
            session_id=request.session_id,
            response=result_state.response,
            response_type=result_state.response_type,
            intent=result_state.intent,
            quiz_active=result_state.quiz.is_active,
            metadata={
                "turn_count": result_state.turn_count,
                "current_topic": result_state.content.subtopic,
                "detected_subject": result_state.content.subject,
                "sources": sources
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Chat error: {e}")
        logger.error(f"Full stack trace:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    tutor_service = Depends(get_tutor_service),
    db_manager = Depends(get_db_manager)
):
    """
    Send a message and get a streaming response from the AI tutor.
    """
    from fastapi.responses import StreamingResponse

    async def event_generator():
        try:
            # Get session
            session = await db_manager.get_session(request.session_id)
            if not session:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Session not found'})}\n\n"
                return

            # Increment message count
            await db_manager.increment_session_messages(request.session_id)

            # Get student info
            student = await db_manager.get_student_by_id(session["student_id"])

            from ..agents.state import ContentContext, StudentContext
            
            state_dict = {
                "session_id": request.session_id,
                "user_input": request.message,
                "student": StudentContext(
                    student_id=session["student_id"],
                    user_id=student["user_id"] if student else "unknown",
                    name=student.get("name") if student else None,
                    grade_level=student.get("grade_level") if student else None,
                    curriculum=student.get("curriculum") if student else None
                ).model_dump(),
                "content": ContentContext(
                    subject=session.get("subject"),
                    subtopic=session.get("current_topic")
                ).model_dump()
            }

            # Run workflow in streaming mode
            async for event in tutor_service.stream(state_dict, config={}):
                if event["type"] == "token":
                    yield f"data: {json.dumps({'type': 'chunk', 'text': event['text']})}\n\n"
                elif event["type"] == "done":
                    # Extract result from done event
                    result_state = event["result"]
                    
                    # Update session with detected subject and topic
                    try:
                        if hasattr(result_state, 'content') or isinstance(result_state, dict):
                            content = getattr(result_state, 'content', result_state.get('content'))
                            subject = getattr(content, 'subject', content.get('subject') if isinstance(content, dict) else None)
                            subtopic = getattr(content, 'subtopic', content.get('subtopic') if isinstance(content, dict) else None)
                            
                            if subject or subtopic:
                                session_updates = {}
                                if subject: session_updates["subject"] = subject
                                if subtopic: session_updates["current_topic"] = subtopic
                                await db_manager.update_session(request.session_id, session_updates)
                    except Exception as e:
                        logger.error(f"Error updating session in stream: {e}")

                    # Yield final completion event
                    yield f"data: {json.dumps({
                        'type': 'done', 
                        'response_type': getattr(result_state, 'response_type', 'text') if hasattr(result_state, 'response_type') else 'text',
                        'sources': getattr(result_state.content, 'rag_results', []) if hasattr(result_state, 'content') else [],
                        'quiz_active': getattr(result_state.quiz, 'is_active', False) if hasattr(result_state, 'quiz') else False
                    })}\n\n"
                elif event["type"] == "error":
                    yield f"data: {json.dumps({'type': 'error', 'message': event['message']})}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ==================== Student Endpoints ====================

@router.get("/student/{user_id}", response_model=StudentProfileResponse)
async def get_student_profile(
    user_id: str,
    db_manager = Depends(get_db_manager)
):
    """Get student profile and learning statistics."""
    try:
        student = await db_manager.get_student_by_user_id(user_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        # Get statistics
        stats = await db_manager.get_student_statistics(student["id"])

        # Get mastery summary
        mastery = await db_manager.get_mastery_scores(student["id"])
        mastery_by_subject = {}
        for m in mastery:
            subj = m.get("subject", "Unknown")
            if subj not in mastery_by_subject:
                mastery_by_subject[subj] = []
            mastery_by_subject[subj].append({
                "topic": m.get("subtopic"),
                "score": m.get("mastery_score"),
                "last_practiced": m.get("last_practiced_at")
            })

        return StudentProfileResponse(
            student_id=student["id"],
            user_id=student["user_id"],
            name=student.get("name"),
            grade_level=student.get("grade_level"),
            curriculum=student.get("curriculum"),
            mastery_summary=mastery_by_subject,
            statistics=stats
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting student profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/student/{user_id}/weak-topics")
async def get_weak_topics(
    user_id: str,
    limit: int = 5,
    db_manager = Depends(get_db_manager)
):
    """Get topics where student needs improvement."""
    try:
        student = await db_manager.get_student_by_user_id(user_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        weak_topics = await db_manager.get_weak_topics(
            student["id"],
            threshold=0.5,
            limit=limit
        )

        return {"weak_topics": weak_topics}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting weak topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/student/{user_id}/review-topics")
async def get_review_topics(
    user_id: str,
    limit: int = 5,
    db_manager = Depends(get_db_manager)
):
    """Get topics due for spaced repetition review."""
    try:
        student = await db_manager.get_student_by_user_id(user_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        review_topics = await db_manager.get_topics_due_for_review(
            student["id"],
            limit=limit
        )

        return {"review_topics": review_topics}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting review topics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Content Endpoints ====================

@router.get("/subjects")
async def list_subjects(
    content_db = Depends(get_content_db)
):
    """List all available subjects from the PostgreSQL content database."""
    try:
        # Fetch directly from PostgreSQL pool if available
        if hasattr(content_db, 'pool') and content_db.pool:
            async with content_db.pool.acquire() as conn:
                rows = await conn.fetch("""
                    SELECT DISTINCT 
                        subject,
                        syllabus,
                        COUNT(*) as topic_count
                    FROM syllabus_hierarchy
                    GROUP BY subject, syllabus
                    ORDER BY subject ASC
                """)
                
                subjects = []
                for i, row in enumerate(rows):
                    subjects.append({
                        "id": i + 1,
                        "name": row['subject'],
                        "syllabus": row['syllabus'],
                        "topic_count": row['topic_count']
                    })
                
                return {"subjects": subjects, "count": len(subjects)}
        
        # Fallback to empty if DB not ready
        return {"subjects": [], "count": 0}
        
    except Exception as e:
        logger.error(f"Error listing subjects from PostgreSQL: {e}")
        # Final fallback - might be useful during migration
        return {"subjects": [], "count": 0}


@router.post("/content/search")
async def search_content(
    request: ContentSearchRequest,
    content_db = Depends(get_content_db)
):
    """Search educational content."""
    try:
        results = await content_db.search_content(
            query=request.query,
            syllabus=request.syllabus,
            subject=request.subject,
            content_type=request.content_type,
            limit=request.limit
        )

        return {"results": results, "count": len(results)}

    except Exception as e:
        logger.error(f"Content search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content/statistics")
async def get_content_statistics(
    content_db = Depends(get_content_db)
):
    """Get content database statistics."""
    try:
        stats = await content_db.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting content stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content/syllabi")
async def list_syllabi(
    content_db = Depends(get_content_db)
):
    """List available syllabi/curricula."""
    try:
        stats = await content_db.get_statistics()
        return {"syllabi": list(stats.get("by_syllabus", {}).keys())}
    except Exception as e:
        logger.error(f"Error listing syllabi: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Health Check ====================

@router.get("/health")
async def health_check():
    """Check tutor service health."""
    return {
        "status": "healthy",
        "service": "ai-tutor",
        "timestamp": datetime.now().isoformat()
    }
