from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from app.db.session import engine, Base

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        # Import models here to ensure they are registered with Base
        from app.models.user import User, Progress
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    return {"message": "Sugarclass Orchestrator API is running", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
