"""
FastAPI Configuration Module
============================
Environment-based configuration for AI Materials service.
"""
import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Application
    APP_NAME: str = "AI Materials API"
    VERSION: str = "2.0.0"
    DEBUG: bool = True
    PORT: int = 8000

    # Project paths
    PROJECT_ROOT: Path = Path(__file__).parent.parent
    BASE_DIR: Path = Path(__file__).parent

    # Database
    DB_NAME: str = "rag_content.db"
    DB_PATH: Path = PROJECT_ROOT / "database" / DB_NAME

    # LLM API Configuration
    LLM_API_URL: str | None = None
    LLM_API_KEY: str | None = None
    LLM_MODEL: str = "gemini-3-pro-preview"

    # OpenAI API (for creative rewriting)
    OPENAI_API_KEY: str | None = None

    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]

    # Frontend
    FRONTEND_DIR: Path = BASE_DIR / "static" / "frontend"

    # Materials directories (optional)
    MATERIALS_DIR: Path = PROJECT_ROOT / "materials"
    MATERIALS_OUTPUT_DIR: Path = PROJECT_ROOT / "output" / "materials_output"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Create settings instance for backward compatibility
settings = get_settings()

# Legacy compatibility - export individual variables
PORT = settings.PORT
DEBUG = settings.DEBUG
DB_PATH = str(settings.DB_PATH)
LLM_API_URL = settings.LLM_API_URL
LLM_API_KEY = settings.LLM_API_KEY
LLM_MODEL = settings.LLM_MODEL
OPENAI_API_KEY = settings.OPENAI_API_KEY
