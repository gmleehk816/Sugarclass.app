import os
import requests
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
        requests.post(
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

@router.post("/generate")
async def generate_quiz(request: QuizGenerationRequest, db: AsyncSession = Depends(get_db)):
    if not request.text:
        raise HTTPException(status_code=400, detail="No source text provided")
    
    questions = await gemini_service.generate_questions(
        text=request.text,
        num_questions=request.num_questions,
        difficulty=request.difficulty
    )
    
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
        "questions": questions
    }

@router.get("/")
async def get_quizzes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Quiz).order_by(Quiz.created_at.desc()))
    return result.scalars().all()

@router.post("/submit")
async def submit_quiz_score(
    quiz_id: str, 
    score: int, 
    total: int, 
    user_id: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    progress = Progress(
        user_id=user_id or "default_user",
        quiz_id=quiz_id,
        score=score,
        total_questions=total
    )
    db.add(progress)
    await db.commit()
    
    # Report to Sugarclass Shell
    if authorization:
        report_activity(
            service="examiner",
            activity_type="quiz_completion",
            token=authorization,
            metadata={"quiz_id": quiz_id, "score": score, "total": total},
            score=round((score/total) * 100) if total > 0 else 0
        )
        
    return {"status": "success", "score": score, "total": total}


