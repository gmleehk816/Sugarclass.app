from typing import Optional, List
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    full_name: Optional[str] = None

class UserCreate(UserBase):
    email: EmailStr
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = None

class User(UserBase):
    id: int
    is_superuser: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

class ProgressBase(BaseModel):
    service: str
    activity_type: str
    metadata_json: Optional[dict] = None
    score: Optional[int] = None

class ProgressCreate(ProgressBase):
    pass

class Progress(ProgressBase):
    id: int
    user_id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# Enhanced stats for dashboard
class ServiceBreakdown(BaseModel):
    service: str
    count: int
    last_used: Optional[datetime] = None
    avg_score: Optional[float] = None

class ActivityTypeBreakdown(BaseModel):
    activity_type: str
    count: int
    service: str

class DailyActivity(BaseModel):
    date: str
    count: int

class StreakInfo(BaseModel):
    current_streak: int
    longest_streak: int
    last_activity_date: Optional[str] = None

class DashboardSummary(BaseModel):
    # Basic stats
    total_activities: int
    last_activity: Optional[Progress] = None

    # Service breakdown with details
    service_stats: dict
    service_breakdown: List[ServiceBreakdown]

    # Activity type breakdown
    activity_types: List[ActivityTypeBreakdown]

    # Time-based stats
    today_activities: int
    this_week_activities: int
    this_month_activities: int

    # Daily activity for chart (last 7 days)
    daily_activity: List[DailyActivity]

    # Streak information
    streak: StreakInfo

    # Performance metrics
    total_quizzes: int
    avg_quiz_score: Optional[float] = None
    best_quiz_score: Optional[int] = None
    
    # Specific metric counters
    total_articles: int = 0
    total_questions: int = 0
    tutor_sessions: int = 0
    unique_subjects: int = 0

    # Recent history
    recent_history: List[Progress]
