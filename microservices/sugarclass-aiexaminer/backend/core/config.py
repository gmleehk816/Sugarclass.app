import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://hb.dockerspeeds.asia"
    LLM_MODEL: str = "gemini-3-flash-preview"
    
    # Database Configuration
    # Production: use PostgreSQL
    # Development: use SQLite
    DB_TYPE: str = os.getenv("DB_TYPE", "sqlite")
    
    # PostgreSQL settings (for production)
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "aiexaminer-db")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "examiner")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "examiner_password")
    
    # SQLite settings (for development)
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "./database/examiner.db")
    
    @property
    def DATABASE_URL(self) -> str:
        """Dynamically construct database URL based on DB_TYPE"""
        if self.DB_TYPE == "postgresql":
            return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        else:
            # Default to SQLite
            return f"sqlite+aiosqlite:///{self.SQLITE_DB_PATH}"
    
    UPLOAD_DIR: str = "uploads"
    MOBILE_BASE_URL: str = "http://localhost:3003"

settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# Ensure database directory exists for SQLite
if settings.DB_TYPE != "postgresql":
    os.makedirs(os.path.dirname(settings.SQLITE_DB_PATH), exist_ok=True)

