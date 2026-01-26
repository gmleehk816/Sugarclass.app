import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://hb.dockerspeeds.asia"
    LLM_MODEL: str = "gemini-3-flash-preview"
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./database/examiner.db"
    UPLOAD_DIR: str = "uploads"
    MOBILE_BASE_URL: str = "http://localhost:3003"

settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
