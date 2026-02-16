"""
AI Materials V8 FastAPI Application
====================================
Educational content management system with V8 enhanced content pipeline.
"""
import os
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .config_fastapi import settings
from .admin import router as admin_router
from .admin_v8 import router as admin_v8_router

# ============================================================================
# Configuration & Paths
# ============================================================================

BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent
# Use DB_PATH from environment variable if set, otherwise use default
DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "database" / "rag_content.db"))

# Static directories
STATIC_DIR = BASE_DIR / "static"
GENERATED_IMAGES_DIR = BASE_DIR / "generated_images"

# Create directories if they don't exist
for directory in [GENERATED_IMAGES_DIR]:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

# ============================================================================
# Database Connection
# ============================================================================

def get_db_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    db_path = str(DB_PATH)
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a database row to a dictionary."""
    return dict(row)

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="AI Materials V8 API",
    description="Educational content management system with V8 enhanced content pipeline",
    version="8.0.0"
)

# ============================================================================
# CORS Middleware
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    import logging
    logger = logging.getLogger("uvicorn")
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include V8 Public Router (no auth - for viewing content)
from .admin_v8 import public_router as v8_public_router
app.include_router(v8_public_router, tags=["V8 Public"])

# Include V8 Admin Router (auth required - for generating/managing content)
app.include_router(admin_v8_router, tags=["V8 Admin"])

# Include Admin Router (old pipeline + task management)
app.include_router(admin_router, tags=["Admin"])

# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Log database path on startup."""
    import logging
    logger = logging.getLogger("uvicorn")
    logger.info(f"AI Materials V8 DB_PATH: {DB_PATH}")
    logger.info(f"Database file exists: {os.path.exists(DB_PATH)}")

    if os.path.exists(DB_PATH):
        logger.info(f"Database size: {os.path.getsize(DB_PATH)} bytes")

        # Check V8 tables
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'v8_%'")
            v8_tables = cursor.fetchall()
            logger.info(f"V8 tables found: {len(v8_tables)}")
            conn.close()
        except Exception as e:
            logger.error(f"Error checking V8 tables: {e}")

# ============================================================================
# Static Files
# ============================================================================

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

if GENERATED_IMAGES_DIR.exists():
    app.mount("/generated_images", StaticFiles(directory=str(GENERATED_IMAGES_DIR)), name="generated_images")

# ============================================================================
# API Routes - Core Hierarchy (V8 compatible)
# ============================================================================

@app.get("/api/topics")
async def get_topics():
    """Get all topics from the database."""
    conn = get_db_connection()
    try:
        topics = conn.execute(
            "SELECT * FROM topics ORDER BY order_num"
        ).fetchall()
        return [row_to_dict(row) for row in topics]
    finally:
        conn.close()

@app.get("/api/topics/{topic_id}/subtopics")
async def get_subtopics(topic_id: str):
    """Get subtopics for a specific topic."""
    conn = get_db_connection()
    try:
        subtopics = conn.execute(
            "SELECT * FROM subtopics WHERE topic_id = ? ORDER BY order_num",
            (topic_id,)
        ).fetchall()
        return [row_to_dict(row) for row in subtopics]
    finally:
        conn.close()

@app.get("/api/db/subjects")
async def get_db_subjects():
    """Get all subjects from the database."""
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT s.id, s.id AS subject_id, s.name, s.code, s.syllabus_id,
                   COUNT(DISTINCT t.id) as topic_count,
                   COUNT(DISTINCT st.id) as subtopic_count
            FROM subjects s
            LEFT JOIN topics t ON t.subject_id = s.id
            LEFT JOIN subtopics st ON st.topic_id = t.id
            GROUP BY s.id
            ORDER BY s.name
        """).fetchall()
        return [row_to_dict(row) for row in rows]
    finally:
        conn.close()

@app.get("/api/db/subjects/{subject_id}/topics")
async def get_db_subject_topics(subject_id: str):
    """Get all topics for a specific subject."""
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT t.id, t.id AS topic_id, t.name, t.subject_id, t.order_num,
                   COUNT(DISTINCT s.id) as subtopic_count
            FROM topics t
            LEFT JOIN subtopics s ON s.topic_id = t.id
            WHERE t.subject_id = ?
            GROUP BY t.id
            ORDER BY t.order_num
        """, (subject_id,)).fetchall()
        return [row_to_dict(row) for row in rows]
    finally:
        conn.close()

@app.get("/api/db/topics/{topic_id}/subtopics")
async def get_db_subtopics(topic_id: str):
    """Get subtopics for a topic with V8 content status."""
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT s.id, s.id AS subtopic_id, s.name, s.topic_id, s.order_num, s.processed_at,
                   (SELECT COUNT(*) FROM v8_concepts WHERE subtopic_id = s.id) as v8_concepts_count
            FROM subtopics s
            WHERE s.topic_id = ?
            ORDER BY s.order_num
        """, (topic_id,)).fetchall()
        return [row_to_dict(row) for row in rows]
    finally:
        conn.close()

@app.get("/api/db/stats")
async def get_db_stats():
    """Get database statistics."""
    conn = get_db_connection()
    try:
        stats = {}
        for table in ['syllabuses', 'subjects', 'topics', 'subtopics',
                      'v8_concepts', 'v8_quiz_questions', 'v8_flashcards', 'v8_reallife_images']:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                stats[table] = count
            except sqlite3.OperationalError:
                stats[table] = 0
        return stats
    finally:
        conn.close()

@app.get("/api/db/subjects/{subject_id}/chapters")
async def get_db_chapters(subject_id: str):
    """Get main chapters for a subject."""
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT t.id, t.name, t.topic_id,
                   COUNT(DISTINCT s.id) as subtopic_count
            FROM topics t
            LEFT JOIN subtopics s ON s.topic_id = t.id
            WHERE t.subject_id = ?
            GROUP BY t.id
            ORDER BY t.order_num
        """, (subject_id,)).fetchall()
        return [row_to_dict(row) for row in rows]
    finally:
        conn.close()

# ============================================================================
# Health Check
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for orchestrator."""
    return {
        "status": "healthy",
        "service": "ai-materials-v8",
        "version": "8.0.0"
    }

# ============================================================================
# Frontend Serving
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the React frontend."""
    frontend_dir = STATIC_DIR / "frontend"
    index_path = frontend_dir / "index.html"

    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding='utf-8'))
    else:
        raise HTTPException(
            status_code=404,
            detail="Frontend not built. Run build script first."
        )

@app.get("/{path:path}", response_class=HTMLResponse)
async def serve_frontend_catchall(path: str):
    """Serve React frontend for client-side routing."""
    frontend_dir = STATIC_DIR / "frontend"
    requested_path = frontend_dir / path

    if requested_path.exists() and requested_path.is_file():
        return HTMLResponse(content=requested_path.read_text(encoding='utf-8'))
    else:
        index_path = frontend_dir / "index.html"
        if index_path.exists():
            return HTMLResponse(content=index_path.read_text(encoding='utf-8'))
        else:
            raise HTTPException(
                status_code=404,
                detail="Frontend not built. Run build script first."
            )

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("AI Materials V8 FastAPI Server starting...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(settings.PORT),
        reload=settings.DEBUG
    )
