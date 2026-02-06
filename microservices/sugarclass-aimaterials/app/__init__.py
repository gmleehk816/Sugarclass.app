"""
AI Materials Application Package
==================================
FastAPI-based educational content management system.
"""
from .main import app
from .config_fastapi import settings

__version__ = settings.VERSION
__all__ = ["app", "settings"]
