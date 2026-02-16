"""
AI Materials FastAPI Server Startup Script
============================================
Run this script to start the FastAPI server.
"""
import uvicorn
from app.config_fastapi import settings

# Run V8 migration on startup
def run_v8_migration():
    """Run V8 database migration if needed."""
    try:
        from app.init_v8_db import migrate_to_v8
        migrate_to_v8()
    except Exception as e:
        print(f"[Startup] V8 migration check failed: {e}")

if __name__ == "__main__":
    # Run migration before starting server
    run_v8_migration()

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
