from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.api import deps
from app.db.session import get_db
from app.models.user import User, Progress
from app.schemas.user import ProgressCreate, Progress as ProgressSchema, DashboardSummary

router = APIRouter()

@router.post("/", response_model=ProgressSchema)
async def create_progress_entry(
    *,
    db: AsyncSession = Depends(get_db),
    progress_in: ProgressCreate,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Create new progress entry.
    """
    db_obj = Progress(
        **progress_in.dict(),
        user_id=current_user.id
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """
    Get unified progress summary for dashboard.
    """
    # Total activities
    count_result = await db.execute(
        select(func.count(Progress.id)).filter(Progress.user_id == current_user.id)
    )
    total_count = count_result.scalar() or 0

    # Last activity
    last_result = await db.execute(
        select(Progress)
        .filter(Progress.user_id == current_user.id)
        .order_by(Progress.timestamp.desc())
        .limit(1)
    )
    last_activity = last_result.scalars().first()

    # Recent history
    history_result = await db.execute(
        select(Progress)
        .filter(Progress.user_id == current_user.id)
        .order_by(Progress.timestamp.desc())
        .limit(10)
    )
    recent_history = history_result.scalars().all()

    # Service stats (count per service)
    stats_result = await db.execute(
        select(Progress.service, func.count(Progress.id))
        .filter(Progress.user_id == current_user.id)
        .group_by(Progress.service)
    )
    service_stats = {row[0]: row[1] for row in stats_result.all()}

    return {
        "total_activities": total_count,
        "last_activity": last_activity,
        "service_stats": service_stats,
        "recent_history": recent_history
    }

@router.get("/history", response_model=List[ProgressSchema])
async def get_full_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(deps.get_current_active_user),
    limit: int = 50
) -> Any:
    """
    Get full activity history.
    """
    result = await db.execute(
        select(Progress)
        .filter(Progress.user_id == current_user.id)
        .order_by(Progress.timestamp.desc())
        .limit(limit)
    )
    return result.scalars().all()
