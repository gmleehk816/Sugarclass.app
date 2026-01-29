import os
import httpx
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.services.gemini_service import gemini_service
from backend.database import get_db
from backend.models.quiz import Quiz, Progress

router = APIRouter()
SUGARCLASS_API_URL = os.getenv("SUGARCLASS_API_URL", "http://backend:8000/api/v1")

def report_activity(service: str, activity_type: str, token: str, metadata: dict = None, score: int = 100):
    if not token:
        return
    try:
        # Use a sync client for this fire-and-forget reporting
        with httpx.Client() as client:
            client.post(
                f"{SUGARCLASS_API_URL}/progress/",
                json={
                    "service": service,
                    "activity_type": activity_type,
                    "metadata_json": metadata or {},
                    "score": score
                },
                headers={"Authorization": token},
                timeout=2
            )
    except Exception as e:
        print(f"Failed to report activity: {e}")


class QuizGenerationRequest(BaseModel):
    text: str
    num_questions: int = 5
    difficulty: str = "medium"
    topic: Optional[str] = None
    material_id: Optional[str] = None
    question_type: str = "mixed"  # "mcq", "short", or "mixed"


class ShortAnswerValidationRequest(BaseModel):
    question: str
    expected_answer: str
    key_points: List[str]
    user_answer: str


class QuestionRegenerateRequest(BaseModel):
    text: str
    existing_questions: List[str]
    question_type: str = "mcq"
    difficulty: str = "medium"


class QuizCreateFromPreviewRequest(BaseModel):
    title: str
    questions: List[dict]
    material_id: Optional[str] = None
    source_text: str


class QuizRenameRequest(BaseModel):
    title: str

class QuizUpdateRequest(BaseModel):
    title: Optional[str] = None
    questions: Optional[List[dict]] = None



@router.post("/generate-preview")
async def generate_quiz_preview(request: QuizGenerationRequest):
    """Generate questions for preview without saving to database"""
    if not request.text:
        raise HTTPException(status_code=400, detail="No source text provided")
    
    questions = []
    
    if request.question_type == "mixed":
        mcq_count = max(1, int(request.num_questions * 0.6))
        short_count = request.num_questions - mcq_count
        
        mcq_questions = await gemini_service.generate_questions(
            text=request.text,
            num_questions=mcq_count,
            difficulty=request.difficulty
        )
        
        short_questions = await gemini_service.generate_short_questions(
            text=request.text,
            num_questions=short_count,
            difficulty=request.difficulty
        )
        
        for q in (mcq_questions or []):
            q['question_type'] = 'mcq'
        for q in (short_questions or []):
            q['question_type'] = 'short'
        
        questions = list(mcq_questions or []) + list(short_questions or [])
                
    elif request.question_type == "short":
        questions = await gemini_service.generate_short_questions(
            text=request.text,
            num_questions=request.num_questions,
            difficulty=request.difficulty
        )
        for q in (questions or []):
            q['question_type'] = 'short'
    else:
        questions = await gemini_service.generate_questions(
            text=request.text,
            num_questions=request.num_questions,
            difficulty=request.difficulty
        )
        for q in (questions or []):
            q['question_type'] = 'mcq'
    
    if not questions:
        raise HTTPException(status_code=500, detail="Failed to generate questions")
        
    return {
        "questions": questions,
        "question_type": request.question_type,
        "topic": request.topic
    }


@router.post("/regenerate-single")
async def regenerate_single_question(request: QuestionRegenerateRequest):
    """Regenerate a single question while avoiding existing ones"""
    
    if request.question_type == "short":
        questions = await gemini_service.generate_short_questions(
            text=request.text,
            num_questions=1,
            difficulty=request.difficulty,
            exclude_questions=request.existing_questions
        )
        if questions:
            questions[0]['question_type'] = 'short'
    else:
        questions = await gemini_service.generate_questions(
            text=request.text,
            num_questions=1,
            difficulty=request.difficulty,
            exclude_questions=request.existing_questions
        )
        if questions:
            questions[0]['question_type'] = 'mcq'
            
    if not questions:
        raise HTTPException(status_code=500, detail="Failed to regenerate question")
        
    return questions[0]


@router.post("/create-from-preview")
async def create_quiz_from_preview(request: QuizCreateFromPreviewRequest, db: AsyncSession = Depends(get_db)):
    """Save approved questions from preview as a new quiz"""
    quiz = Quiz(
        title=request.title,
        source_text=request.source_text,
        questions=request.questions,
        material_id=request.material_id
    )
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)
    
    return {
        "id": quiz.id,
        "title": quiz.title,
        "questions": quiz.questions
    }


@router.patch("/{quiz_id}")
async def update_quiz(quiz_id: str, request: QuizUpdateRequest, db: AsyncSession = Depends(get_db)):
    """Update quiz title and/or questions"""
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Update fields if provided
    if request.title is not None:
        quiz.title = request.title
    if request.questions is not None:
        quiz.questions = request.questions
    
    await db.commit()
    await db.refresh(quiz)
    
    return {"status": "success", "id": quiz.id, "title": quiz.title, "questions": quiz.questions}


@router.get("/{quiz_id}")
async def get_quiz(quiz_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific quiz by ID"""
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    return {
        "id": quiz.id,
        "title": quiz.title,
        "questions": quiz.questions,
        "material_id": quiz.material_id,
        "created_at": quiz.created_at
    }


@router.post("/generate")
async def generate_quiz(request: QuizGenerationRequest, db: AsyncSession = Depends(get_db)):
    if not request.text:
        raise HTTPException(status_code=400, detail="No source text provided")
    
    questions = []
    
    # Generate based on question type
    if request.question_type == "mixed":
        # Split questions between MCQ and Short Answer (roughly 60/40 split)
        mcq_count = max(1, int(request.num_questions * 0.6))
        short_count = request.num_questions - mcq_count
        
        mcq_questions = await gemini_service.generate_questions(
            text=request.text,
            num_questions=mcq_count,
            difficulty=request.difficulty
        )
        
        short_questions = await gemini_service.generate_short_questions(
            text=request.text,
            num_questions=short_count,
            difficulty=request.difficulty
        )
        
        # Mark each question with its type for the frontend
        for q in (mcq_questions or []):
            q['question_type'] = 'mcq'
        for q in (short_questions or []):
            q['question_type'] = 'short'
        
        # Group questions by type: MCQ first, then Short Answer
        questions = list(mcq_questions or []) + list(short_questions or [])
                
    elif request.question_type == "short":
        questions = await gemini_service.generate_short_questions(
            text=request.text,
            num_questions=request.num_questions,
            difficulty=request.difficulty
        )
        for q in (questions or []):
            q['question_type'] = 'short'
    else:
        questions = await gemini_service.generate_questions(
            text=request.text,
            num_questions=request.num_questions,
            difficulty=request.difficulty
        )
        for q in (questions or []):
            q['question_type'] = 'mcq'
    
    if not questions:
        raise HTTPException(status_code=500, detail="Failed to generate questions")
    
    quiz = Quiz(
        title=request.topic or "Untitled Quiz",
        source_text=request.text,
        questions=questions,
        material_id=request.material_id
    )
    db.add(quiz)
    await db.commit()
    await db.refresh(quiz)
        
    return {
        "id": quiz.id,
        "questions": questions,
        "question_type": request.question_type
    }


@router.post("/validate-short-answer")
async def validate_short_answer(request: ShortAnswerValidationRequest):
    """Validate a user's short answer response using AI"""
    
    result = await gemini_service.validate_short_answer(
        question=request.question,
        expected_answer=request.expected_answer,
        key_points=request.key_points,
        user_answer=request.user_answer
    )
    
    return result


@router.get("/")
async def get_quizzes(
    limit: int = 100, 
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Quiz)
        .order_by(Quiz.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()


@router.get("/{quiz_id}")
async def get_quiz_by_id(quiz_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch a specific quiz by ID to replay it"""
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    return {
        "id": quiz.id,
        "title": quiz.title,
        "questions": quiz.questions,
        "material_id": quiz.material_id,
        "created_at": quiz.created_at
    }


@router.delete("/{quiz_id}")
async def delete_quiz(quiz_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a specific quiz and its related progress"""
    # Delete the quiz
    result = await db.execute(select(Quiz).where(Quiz.id == quiz_id))
    quiz = result.scalar_one_or_none()
    
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    await db.delete(quiz)
    
    # Also delete any related progress records
    from sqlalchemy import delete
    from backend.models.quiz import Progress
    await db.execute(delete(Progress).where(Progress.quiz_id == quiz_id))
    
    await db.commit()
    
    return {"status": "success", "message": "Quiz deleted successfully"}



class QuizSubmitRequest(BaseModel):
    quiz_id: str
    score: int
    total: int
    user_id: Optional[str] = None
    question_type: Optional[str] = "mcq"


@router.post("/submit")
async def submit_quiz_score(
    request: QuizSubmitRequest,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    progress = Progress(
        user_id=request.user_id or "default_user",
        quiz_id=request.quiz_id,
        score=request.score,
        total_questions=request.total
    )
    db.add(progress)
    await db.commit()
    
    # Report to Sugarclass Shell
    if authorization:
        report_activity(
            service="examiner",
            activity_type="quiz_completion",
            token=authorization,
            metadata={
                "quiz_id": request.quiz_id, 
                "score": request.score, 
                "total": request.total,
                "question_type": request.question_type
            },
            score=round((request.score/request.total) * 100) if request.total > 0 else 0
        )
        
    return {"status": "success", "score": request.score, "total": request.total}
