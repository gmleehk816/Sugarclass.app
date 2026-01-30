from typing import Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date

from app.api import deps
from app.db.session import get_db
from app.models.user import User, Progress
from app.schemas.user import (
    ProgressCreate,
    Progress as ProgressSchema,
    DashboardSummary,
    ServiceBreakdown,
    ActivityTypeBreakdown,
    DailyActivity,
    StreakInfo
)

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
    Get unified progress summary for dashboard with detailed stats.
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

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

    # Service breakdown with last used and avg score
    service_breakdown = []
    for service in ['tutor', 'writer', 'examiner']:
        svc_count = service_stats.get(service, 0)

        # Get last used timestamp for this service
        last_used_result = await db.execute(
            select(Progress.timestamp)
            .filter(Progress.user_id == current_user.id, Progress.service == service)
            .order_by(Progress.timestamp.desc())
            .limit(1)
        )
        last_used = last_used_result.scalar()

        # Get avg score for examiner
        avg_score = None
        if service == 'examiner':
            avg_result = await db.execute(
                select(func.avg(Progress.score))
                .filter(
                    Progress.user_id == current_user.id,
                    Progress.service == 'examiner',
                    Progress.score.isnot(None)
                )
            )
            avg_score = avg_result.scalar()

        service_breakdown.append(ServiceBreakdown(
            service=service,
            count=svc_count,
            last_used=last_used,
            avg_score=round(avg_score, 1) if avg_score else None
        ))

    # Activity type breakdown
    activity_type_result = await db.execute(
        select(Progress.activity_type, Progress.service, func.count(Progress.id))
        .filter(Progress.user_id == current_user.id)
        .group_by(Progress.activity_type, Progress.service)
    )
    activity_types = [
        ActivityTypeBreakdown(activity_type=row[0], service=row[1], count=row[2])
        for row in activity_type_result.all()
    ]

    # Today's activities
    today_result = await db.execute(
        select(func.count(Progress.id))
        .filter(Progress.user_id == current_user.id, Progress.timestamp >= today_start)
    )
    today_activities = today_result.scalar() or 0

    # This week's activities
    week_result = await db.execute(
        select(func.count(Progress.id))
        .filter(Progress.user_id == current_user.id, Progress.timestamp >= week_start)
    )
    this_week_activities = week_result.scalar() or 0

    # This month's activities
    month_result = await db.execute(
        select(func.count(Progress.id))
        .filter(Progress.user_id == current_user.id, Progress.timestamp >= month_start)
    )
    this_month_activities = month_result.scalar() or 0

    # Daily activity for last 7 days
    daily_activity = []
    for i in range(6, -1, -1):
        day_start = today_start - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        day_result = await db.execute(
            select(func.count(Progress.id))
            .filter(
                Progress.user_id == current_user.id,
                Progress.timestamp >= day_start,
                Progress.timestamp < day_end
            )
        )
        daily_activity.append(DailyActivity(
            date=day_start.strftime("%Y-%m-%d"),
            count=day_result.scalar() or 0
        ))

    # Calculate streak
    streak_info = await calculate_streak(db, current_user.id, today_start)

    # Quiz specific stats
    quiz_count_result = await db.execute(
        select(func.count(Progress.id))
        .filter(
            Progress.user_id == current_user.id,
            Progress.service == 'examiner'
        )
    )
    total_quizzes = quiz_count_result.scalar() or 0

    avg_quiz_result = await db.execute(
        select(func.avg(Progress.score))
        .filter(
            Progress.user_id == current_user.id,
            Progress.service == 'examiner',
            Progress.score.isnot(None)
        )
    )
    avg_quiz_score = avg_quiz_result.scalar()

    best_quiz_result = await db.execute(
        select(func.max(Progress.score))
        .filter(
            Progress.user_id == current_user.id,
            Progress.service == 'examiner',
            Progress.score.isnot(None)
        )
    )
    best_quiz_score = best_quiz_result.scalar()

    return {
        "total_activities": total_count,
        "last_activity": last_activity,
        "service_stats": service_stats,
        "service_breakdown": service_breakdown,
        "activity_types": activity_types,
        "today_activities": today_activities,
        "this_week_activities": this_week_activities,
        "this_month_activities": this_month_activities,
        "daily_activity": daily_activity,
        "streak": streak_info,
        "total_quizzes": total_quizzes,
        "avg_quiz_score": round(avg_quiz_score, 1) if avg_quiz_score else None,
        "best_quiz_score": best_quiz_score,
        "recent_history": recent_history
    }


async def calculate_streak(db: AsyncSession, user_id: int, today_start: datetime) -> StreakInfo:
    """Calculate current and longest streak for a user."""
    # Get all unique activity dates
    dates_result = await db.execute(
        select(func.date(Progress.timestamp))
        .filter(Progress.user_id == user_id)
        .group_by(func.date(Progress.timestamp))
        .order_by(func.date(Progress.timestamp).desc())
    )
    activity_dates = [row[0] for row in dates_result.all()]

    if not activity_dates:
        return StreakInfo(current_streak=0, longest_streak=0, last_activity_date=None)

    # Convert to date objects if they're strings
    activity_dates = [
        datetime.strptime(d, "%Y-%m-%d").date() if isinstance(d, str) else d
        for d in activity_dates
    ]

    today = today_start.date()
    yesterday = today - timedelta(days=1)

    # Calculate current streak
    current_streak = 0
    last_date = activity_dates[0] if activity_dates else None

    # Check if streak is active (activity today or yesterday)
    if last_date and (last_date == today or last_date == yesterday):
        check_date = last_date
        for activity_date in activity_dates:
            if activity_date == check_date:
                current_streak += 1
                check_date = check_date - timedelta(days=1)
            elif activity_date < check_date:
                break

    # Calculate longest streak
    longest_streak = 0
    if activity_dates:
        streak = 1
        sorted_dates = sorted(set(activity_dates))
        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                streak += 1
            else:
                longest_streak = max(longest_streak, streak)
                streak = 1
        longest_streak = max(longest_streak, streak)

    return StreakInfo(
        current_streak=current_streak,
        longest_streak=longest_streak,
        last_activity_date=str(last_date) if last_date else None
    )


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
