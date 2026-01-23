from fastapi import APIRouter
from app.api.v1.endpoints import auth, progress

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(progress.router, prefix="/progress", tags=["progress"])
