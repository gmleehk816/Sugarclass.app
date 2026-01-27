from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from backend.database import get_db
from backend.models.quiz import Progress, Quiz
from typing import Optional

router = APIRouter()

@router.get("/")
async def get_user_progress(user_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    user_id = user_id or "default_user"
    
    # Total Quizzes
    count_result = await db.execute(
        select(func.count(Progress.id)).where(Progress.user_id == user_id)
    )
    total_quizzes = count_result.scalar() or 0
    
    # Average Accuracy
    acc_result = await db.execute(
        select(func.avg(Progress.score * 1.0 / Progress.total_questions))
        .where(Progress.user_id == user_id)
    )
    avg_accuracy = acc_result.scalar() or 0
    
    # Historical List
    hist_result = await db.execute(
        select(Progress, Quiz.title, Quiz.material_id)
        .join(Quiz, Progress.quiz_id == Quiz.id)
        .where(Progress.user_id == user_id)
        .order_by(Progress.completed_at.desc())
    )
    
    history = []
    for row, title, material_id in hist_result:
        history.append({
            "id": row.id,
            "title": title,
            "material_id": material_id,
            "score": row.score,
            "total": row.total_questions,
            "accuracy": f"{round((row.score/row.total_questions)*100)}%",
            "completed_at": row.completed_at.isoformat()
        })
        
    return {
        "quizzes_taken": total_quizzes,
        "average_accuracy": f"{round(avg_accuracy * 100)}%",
        "history": history
    }
