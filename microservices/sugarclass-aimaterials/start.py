"""
AI Materials FastAPI Server Startup Script
============================================
Run this script to start the FastAPI server.
"""
import uvicorn
from app.config_fastapi import settings

if __name__ == "__main__":
    print(f"""
    ╔═══════════════════════════════════════════════════════════════╗
    ║   AI Materials FastAPI Server                                 ║
    ║   Version: {settings.VERSION}                                      ║
    ║   Port: {settings.PORT}                                                ║
    ║   Debug: {settings.DEBUG}                                                  ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
