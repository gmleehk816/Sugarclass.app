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

class DashboardSummary(BaseModel):
    total_activities: int
    last_activity: Optional[Progress] = None
    service_stats: dict
    recent_history: List[Progress]
