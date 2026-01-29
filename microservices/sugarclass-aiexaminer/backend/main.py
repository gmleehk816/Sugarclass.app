from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from backend.database import engine, Base
from backend.api.endpoints import quiz, upload, progress, collections
import backend.models.quiz

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Sugarclass AI Examiner API",
    description="Backend API for AI-powered exam preparation",
    version="1.0.0"
)

@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3400,http://localhost:3403")
allow_origins_list = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router, prefix="/v1/upload", tags=["upload"])
app.include_router(quiz.router, prefix="/v1/quiz", tags=["quiz"])
app.include_router(progress.router, prefix="/v1/progress", tags=["progress"])
app.include_router(collections.router, prefix="/v1/collections", tags=["collections"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "ai-examiner"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
