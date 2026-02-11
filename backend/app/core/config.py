from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Sugarclass Orchestrator"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY") # No default in production!
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day (reduced from 7 days)
    
    # DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/sugarclass")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./sugarclass.db")

    # Restricted CORS for security
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3400",
        "http://localhost:3401",
        "http://localhost:3402",
        "http://localhost:3403",
        "http://localhost:3404",
        "https://sugarclass.app", # Final domain
    ]

    # External Service URLs (Stubs for now)
    AI_TUTOR_URL: str = os.getenv("AI_TUTOR_URL", "http://localhost:8001")
    AI_WRITER_URL: str = os.getenv("AI_WRITER_URL", "http://localhost:8001")
    AI_EXAMINER_URL: str = os.getenv("AI_EXAMINER_URL", "http://localhost:8003")

    class Config:
        case_sensitive = True

settings = Settings()
