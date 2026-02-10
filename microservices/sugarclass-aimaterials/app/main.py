"""
AI Materials FastAPI Application
==================================
Educational content management system with LLM-powered content enhancement.
"""
import os
import sqlite3
import json
import markdown
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config_fastapi import settings
from .admin import router as admin_router

# ============================================================================
# Configuration & Paths
# ============================================================================

BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent
# Use DB_PATH from environment variable if set, otherwise use default
DB_PATH = Path(os.getenv("DB_PATH", PROJECT_ROOT / "database" / "rag_content.db"))

# Static directories
STATIC_DIR = BASE_DIR / "static"
GENERATED_IMAGES_DIR = BASE_DIR / "generated_images"
STATIC_GENERATED_IMAGES_DIR = STATIC_DIR / "generated_images"
EXERCISE_IMAGES_DIR = BASE_DIR / "exercise_images"

# Create directories if they don't exist (skip if read-only filesystem)
for directory in [GENERATED_IMAGES_DIR, STATIC_GENERATED_IMAGES_DIR, EXERCISE_IMAGES_DIR]:
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError:
        # Directory creation may fail in read-only containers; directories should be pre-created in Dockerfile
        pass

# Materials directories (optional, may not exist in production)
MATERIALS_DIR = PROJECT_ROOT / "materials"
MATERIALS_OUTPUT_DIR = PROJECT_ROOT / "output" / "materials_output"

# ============================================================================
# Database Connection
# ============================================================================

def get_db_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    db_path = str(DB_PATH)
    # Check if database file exists
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found at: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="AI Materials API",
    description="Educational content management system with LLM-powered enhancement",
    version="2.0.0"
)

# ============================================================================
# CORS Middleware
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    import logging
    logger = logging.getLogger("uvicorn")
    logger.error(f"Validation error: {exc.errors()}")
    logger.error(f"Request body: {await request.body()}")
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

# Include Admin Router
app.include_router(admin_router)

# ============================================================================
# Startup Event
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Log database path on startup and initialize database if needed."""
    import logging
    logger = logging.getLogger("uvicorn")
    logger.info(f"AI Materials DB_PATH: {DB_PATH}")
    logger.info(f"Database file exists: {os.path.exists(DB_PATH)}")
    
    # Initialize database if it doesn't exist or is missing tables
    try:
        # Import the init function
        from .processors.content_splitter import init_database as init_db_tables
        
        # Check if tables exist
        needs_init = False
        if not os.path.exists(DB_PATH):
            logger.info("Database file not found, will create with tables")
            # Create directory if it doesn't exist
            DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            needs_init = True
        else:
            logger.info(f"Database size: {os.path.getsize(DB_PATH)} bytes")
            # Check if subtopics table exists
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subtopics'")
                if not cursor.fetchone():
                    logger.warning("subtopics table not found, will initialize tables")
                    needs_init = True
                conn.close()
            except Exception as e:
                logger.error(f"Error checking database tables: {e}")
                needs_init = True
        
        if needs_init:
            logger.info("Initializing database tables...")
            init_db_tables(DB_PATH)
            logger.info("✅ Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

# ============================================================================
# Static Files
# ============================================================================

# Mount static directories
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

if GENERATED_IMAGES_DIR.exists():
    app.mount("/generated_images", StaticFiles(directory=str(GENERATED_IMAGES_DIR)), name="generated_images")

if EXERCISE_IMAGES_DIR.exists():
    app.mount("/exercise_images", StaticFiles(directory=str(EXERCISE_IMAGES_DIR)), name="exercise_images")

# ============================================================================
# Pydantic Models
# ============================================================================

class ContentResponse(BaseModel):
    """Response model for content endpoints."""
    id: Optional[int] = None
    subtopic_id: str
    subtopic_name: str
    topic_name: Optional[str] = None
    html_content: Optional[str] = None
    markdown_content: Optional[str] = None
    summary: Optional[str] = None
    is_processed: bool = False
    processor_version: Optional[str] = None

class RewriteRequest(BaseModel):
    """Request model for rewrite endpoint."""
    force: bool = False

class RewriteResponse(BaseModel):
    """Response model for rewrite endpoint."""
    success: bool
    subtopic_id: str
    message: str
    result: Optional[Dict[str, Any]] = None

# ============================================================================
# Helper Functions
# ============================================================================

def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert a database row to a dictionary."""
    return dict(row)

def safe_json_loads(value: Optional[str]) -> Any:
    """Safely parse JSON string."""
    if value:
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            pass
    return value

def normalize_options(options: Any, correct_answer: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Normalize options to standard array format.

    Handles multiple input formats:
    - Object: {"A": "Option A", "B": "Option B"} with correct_answer="B"
    - String: "A. Option A\nB. Option B" with correct_answer="B"
    - Array: [{"text": "A", "is_correct": false}, ...] (already normalized)

    Returns: [{"text": "Option A", "is_correct": false}, ...]
    """
    # If already in array format, check if it has the correct structure
    if isinstance(options, list):
        if options and isinstance(options[0], dict) and 'is_correct' in options[0]:
            return options
        # If it's a list but not in our format, try to convert
        return [{"text": str(opt), "is_correct": False} for opt in options]

    # If it's an object like {"A": "...", "B": "..."}
    if isinstance(options, dict):
        result = []
        for key, value in options.items():
            is_correct = correct_answer and str(key).upper() == str(correct_answer).upper()
            result.append({"text": value, "is_correct": is_correct})
        return result

    # If it's a string like "A. Option A\nB. Option B"
    if isinstance(options, str):
        import re
        # Pattern to match "A." or "A)" or "A)" at the start of lines
        pattern = r'^([A-Z])[.)]\s*(.+?)$'
        lines = options.strip().split('\n')
        result = []
        for line in lines:
            match = re.match(pattern, line.strip())
            if match:
                letter, text = match.groups()
                is_correct = correct_answer and letter.upper() == str(correct_answer).upper()
                result.append({"text": text, "is_correct": is_correct})
            elif line.strip():
                # Fallback for lines without letter prefix
                result.append({"text": line.strip(), "is_correct": False})
        return result if result else [{"text": options, "is_correct": False}]

    # Fallback: return empty array
    return []

def extract_body_content(html: Optional[str]) -> Optional[str]:
    """
    Extract body content from full HTML documents.

    If the HTML contains <body> tags, extract only the body content.
    Otherwise, return the HTML as-is.

    This is needed when inserting HTML into a div using dangerouslySetInnerHTML,
    as browsers don't render nested <html> tags correctly.
    """
    if not html:
        return None

    html = html.strip()

    # Check if it's a full HTML document
    if '<body' in html.lower():
        try:
            import re
            # Extract content between <body> and </body>
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
            if body_match:
                body_content = body_match.group(1).strip()
                return body_content
        except Exception:
            pass

    return html

# ============================================================================
# API Routes - Content
# ============================================================================

@app.get("/api/topics", response_model=List[Dict[str, Any]])
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

@app.get("/api/topics/{topic_id}/subtopics", response_model=List[Dict[str, Any]])
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

@app.get("/api/content/{subtopic_id}")
async def get_content(subtopic_id: str):
    """Legacy route - redirects to DB content endpoint."""
    return await get_db_content(subtopic_id)

@app.get("/api/topics/{topic_id}/questions", response_model=List[Dict[str, Any]])
async def get_questions(topic_id: str):
    """Get questions for a topic."""
    conn = get_db_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM questions WHERE topic_id LIKE ? ORDER BY id",
            (f"%{topic_id}%",)
        ).fetchall()

        questions = []
        for row in rows:
            q = row_to_dict(row)
            raw_options = safe_json_loads(q.get('options'))
            correct_answer = q.get('correct_answer')
            q['options'] = normalize_options(raw_options, correct_answer)
            q['meta'] = safe_json_loads(q.get('meta'))
            questions.append(q)

        return questions
    finally:
        conn.close()

@app.get("/api/subtopics", response_model=List[Dict[str, Any]])
async def get_all_subtopics():
    """Get all subtopics with status information."""
    conn = get_db_connection()
    try:
        query = """
            SELECT s.*, t.name as topic_name, t.type as topic_type,
                   CASE WHEN c.id IS NOT NULL THEN 1 ELSE 0 END as has_content
            FROM subtopics s
            LEFT JOIN topics t ON s.topic_id = t.id
            LEFT JOIN content c ON s.id = c.subtopic_id
            ORDER BY t.order_num, s.order_num
        """
        rows = conn.execute(query).fetchall()
        return [row_to_dict(row) for row in rows]
    finally:
        conn.close()

# ============================================================================
# API Routes - Database
# ============================================================================

@app.get("/api/db/subjects", response_model=List[Dict[str, Any]])
async def get_db_subjects():
    """Get all subjects from the database with counts."""
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT s.id, s.name, s.syllabus_id, 'N/A' as code,
                   COUNT(DISTINCT t.id) as topic_count,
                   COUNT(DISTINCT st.id) as subtopic_count,
                   COUNT(DISTINCT cr.id) as processed_count
            FROM subjects s
            LEFT JOIN topics t ON t.subject_id = s.id
            LEFT JOIN subtopics st ON st.topic_id = t.id
            LEFT JOIN content_raw cr ON cr.subtopic_id = st.id
            GROUP BY s.id
            ORDER BY s.name
        """).fetchall()
        return [row_to_dict(row) for row in rows]
    finally:
        conn.close()

@app.get("/api/db/tree")
async def get_db_tree():
    """Get all subjects grouped by syllabus for filesystem tree view."""
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT s.id, s.name, s.syllabus_id,
                   COUNT(DISTINCT t.id) as topic_count,
                   COUNT(DISTINCT st.id) as subtopic_count,
                   COUNT(DISTINCT cr.id) as content_count
            FROM subjects s
            LEFT JOIN topics t ON t.subject_id = s.id
            LEFT JOIN subtopics st ON st.topic_id = t.id
            LEFT JOIN content_raw cr ON cr.subtopic_id = st.id
            GROUP BY s.id
            ORDER BY s.syllabus_id, s.name
        """).fetchall()
        return [row_to_dict(row) for row in rows]
    finally:
        conn.close()

@app.get("/api/db/subjects/{subject_id}/chapters", response_model=List[Dict[str, Any]])
async def get_db_chapters(subject_id: str):
    """Get main chapters for a subject."""
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT t.id, t.name,
                   SUBSTR(t.name, 1, 1) as chapter_num,
                   COUNT(DISTINCT s.id) as subtopic_count,
                   COUNT(DISTINCT cr.id) as content_count
            FROM topics t
            LEFT JOIN subtopics s ON s.topic_id = t.id
            LEFT JOIN content_raw cr ON cr.subtopic_id = s.id
            WHERE t.subject_id = ?
              AND t.name GLOB '[0-9] *'
              AND t.name NOT LIKE '%.%'
            GROUP BY t.id
            ORDER BY CAST(SUBSTR(t.name, 1, 1) AS INTEGER)
        """, (subject_id,)).fetchall()
        return [row_to_dict(row) for row in rows]
    finally:
        conn.close()

@app.get("/api/db/subjects/{subject_id}/topics", response_model=List[Dict[str, Any]])
async def get_db_subject_topics(subject_id: str):
    """Get all topics for a specific subject."""
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT t.id, t.name, 'topic' as type, t.subject_id,
                   COALESCE(t.order_num, 9999) as order_num,
                   COUNT(DISTINCT s.id) as subtopic_count,
                   COUNT(DISTINCT cr.id) as processed_count
            FROM topics t
            LEFT JOIN subtopics s ON s.topic_id = t.id
            LEFT JOIN content_raw cr ON cr.subtopic_id = s.id
            WHERE t.subject_id = ?
              AND (t.type = 'Chapter' OR t.order_num IS NOT NULL OR t.name LIKE '%SECTION%')
            GROUP BY t.id
            ORDER BY COALESCE(t.order_num, 9999)
        """, (subject_id,)).fetchall()
        return [row_to_dict(row) for row in rows]
    finally:
        conn.close()

@app.get("/api/db/topics", response_model=List[Dict[str, Any]])
async def get_db_topics():
    """Get all topics from the database."""
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT t.id, t.name, 'topic' as type, t.subject_id,
                   COALESCE(t.order_num, 999) as order_num,
                   COUNT(DISTINCT s.id) as subtopic_count,
                   COUNT(DISTINCT cr.id) as processed_count
            FROM topics t
            LEFT JOIN subtopics s ON s.topic_id = t.id
            LEFT JOIN content_raw cr ON cr.subtopic_id = s.id
            GROUP BY t.id
            ORDER BY t.order_num
        """).fetchall()
        return [row_to_dict(row) for row in rows]
    finally:
        conn.close()

@app.get("/api/db/topics/{topic_id}/subtopics", response_model=List[Dict[str, Any]])
async def get_db_subtopics(topic_id: str):
    """Get subtopics for a topic with content status."""
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT s.id, s.name, s.topic_id, s.order_num,
                   (SELECT id FROM content_raw WHERE subtopic_id = s.id LIMIT 1) as raw_id,
                   (SELECT LENGTH(markdown_content) FROM content_raw WHERE subtopic_id = s.id LIMIT 1) as raw_chars,
                   (SELECT id FROM content_processed WHERE subtopic_id = s.id LIMIT 1) as processed_id,
                   (SELECT LENGTH(html_content) FROM content_processed WHERE subtopic_id = s.id LIMIT 1) as processed_chars
            FROM subtopics s
            WHERE s.topic_id = ?
            ORDER BY s.order_num
        """, (topic_id,)).fetchall()
        return [row_to_dict(row) for row in rows]
    finally:
        conn.close()

@app.get("/api/db/content/{subtopic_id}")
async def get_db_content(subtopic_id: str, mode: str = Query("processed", description="Content mode: 'raw' or 'processed'")):
    """Get content for a subtopic from the database."""
    conn = get_db_connection()
    try:
        # Get raw content
        row = conn.execute("""
            SELECT cr.id, cr.subtopic_id, cr.markdown_content, cr.title,
                   s.name as subtopic_name, t.name as topic_name
            FROM content_raw cr
            LEFT JOIN subtopics s ON s.id = cr.subtopic_id
            LEFT JOIN topics t ON s.topic_id = t.id
            WHERE cr.subtopic_id LIKE ?
        """, (f"%{subtopic_id}%",)).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Content not found")

        row_dict = row_to_dict(row)
        actual_subtopic_id = row_dict['subtopic_id']

        # Get processed content
        processed_row = conn.execute("""
            SELECT html_content, summary, processor_version
            FROM content_processed
            WHERE subtopic_id = ?
            LIMIT 1
        """, (actual_subtopic_id,)).fetchone()

        # Determine response based on mode
        if mode == "raw":
            return {
                "id": row_dict['id'],
                "subtopic_id": actual_subtopic_id,
                "subtopic_name": row_dict.get('subtopic_name') or row_dict.get('title'),
                "topic_name": row_dict.get('topic_name'),
                "markdown_content": row_dict['markdown_content'],
                "html_content": None,
                "summary": row_dict.get('subtopic_name') or row_dict.get('title'),
                "is_processed": False
            }
        else:
            # Convert to HTML if needed
            html = None
            if processed_row:
                html = extract_body_content(processed_row['html_content'])

            if not html and row_dict.get('markdown_content'):
                html = markdown.markdown(
                    row_dict['markdown_content'],
                    extensions=['tables', 'fenced_code']
                )

            return {
                "id": row_dict['id'],
                "subtopic_id": actual_subtopic_id,
                "subtopic_name": row_dict.get('subtopic_name') or row_dict.get('title'),
                "topic_name": row_dict.get('topic_name'),
                "description": "",
                "html_content": html,
                "markdown_content": row_dict['markdown_content'],
                "summary": processed_row['summary'] if processed_row else (row_dict.get('subtopic_name') or row_dict.get('title')),
                "is_processed": processed_row is not None,
                "processor_version": processed_row['processor_version'] if processed_row else None
            }
    finally:
        conn.close()

@app.get("/api/db/stats")
async def get_db_stats():
    """Get database statistics."""
    conn = get_db_connection()
    try:
        stats = {}
        for table in ['syllabuses', 'subjects', 'topics', 'subtopics', 'content_raw', 'content_processed']:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                stats[table] = count
            except sqlite3.OperationalError:
                stats[table] = 0
        return stats
    finally:
        conn.close()

@app.get("/api/db/subjects/{subject_id}/all-subtopics")
async def get_all_subtopics_for_subject(subject_id: str):
    """Get all subtopics for a subject with chapter info."""
    conn = get_db_connection()
    try:
        rows = conn.execute("""
            SELECT
                s.id, s.name, s.topic_id, s.order_num,
                t.id as chapter_id, t.order_num as chapter_num, t.name as chapter_title,
                (SELECT COUNT(*) FROM content_raw WHERE subtopic_id = s.id) > 0 as has_content,
                (SELECT COUNT(*) FROM content_processed WHERE subtopic_id = s.id) > 0 as has_rewrite
            FROM subtopics s
            JOIN topics t ON s.topic_id = t.id
            WHERE t.subject_id = ?
            ORDER BY t.order_num, s.order_num
        """, (subject_id,)).fetchall()
        return {"subtopics": [row_to_dict(row) for row in rows]}
    finally:
        conn.close()

# ============================================================================
# API Routes - Exercises
# ============================================================================

@app.get("/api/exercises/{subtopic_id}", response_model=List[Dict[str, Any]])
async def get_exercises(subtopic_id: str):
    """Get exercises for a subtopic."""
    conn = get_db_connection()
    try:
        # Check if table exists
        table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='exercises'"
        ).fetchone()

        if not table_exists:
            return []

        rows = conn.execute(
            "SELECT * FROM exercises WHERE subtopic_id LIKE ? ORDER BY question_num",
            (f"%{subtopic_id}%",)
        ).fetchall()

        exercises = []
        for row in rows:
            ex = row_to_dict(row)
            raw_options = safe_json_loads(ex.get('options'))
            correct_answer = ex.get('correct_answer')
            ex['options'] = normalize_options(raw_options, correct_answer)
            exercises.append(ex)

        return exercises
    finally:
        conn.close()

@app.get("/api/topics/{topic_id}/exercises", response_model=List[Dict[str, Any]])
async def get_topic_exercises(topic_id: str):
    """Get all exercises for subtopics under a topic."""
    conn = get_db_connection()
    try:
        table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='exercises'"
        ).fetchone()

        if not table_exists:
            return []

        rows = conn.execute("""
            SELECT e.*, s.name as subtopic_name
            FROM exercises e
            JOIN subtopics s ON s.id = e.subtopic_id
            WHERE e.subtopic_id LIKE ?
            ORDER BY e.subtopic_id, e.question_num
        """, (f"%{topic_id}%",)).fetchall()

        exercises = []
        for row in rows:
            ex = row_to_dict(row)
            raw_options = safe_json_loads(ex.get('options'))
            correct_answer = ex.get('correct_answer')
            ex['options'] = normalize_options(raw_options, correct_answer)
            exercises.append(ex)

        return exercises
    finally:
        conn.close()

# ============================================================================
# API Routes - Creative Rewrite
# ============================================================================

@app.get("/api/content/{subtopic_id}/with-rewrite")
async def get_content_with_rewrite(subtopic_id: str):
    """Get both raw and processed content for a subtopic."""
    conn = get_db_connection()
    try:
        # Get raw content
        row = conn.execute("""
            SELECT cr.id, cr.subtopic_id, cr.markdown_content, cr.title,
                   s.name as subtopic_name,
                   t.name as topic_name, t.id as topic_id
            FROM content_raw cr
            LEFT JOIN subtopics s ON s.id = cr.subtopic_id
            LEFT JOIN topics t ON s.topic_id = t.id
            WHERE cr.subtopic_id LIKE ?
        """, (f"%{subtopic_id}%",)).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Content not found")

        content_data = row_to_dict(row)
        actual_subtopic_id = content_data['subtopic_id']

        # Get processed content with priority ordering
        processed_row = conn.execute("""
            SELECT * FROM content_processed
            WHERE subtopic_id = ?
            ORDER BY
                CASE
                    WHEN processor_version LIKE '%creative%' THEN 1
                    WHEN processor_version LIKE '%hybrid-gemini-2.5%' THEN 2
                    WHEN processor_version LIKE '%gemini-3-flash%' THEN 3
                    WHEN processor_version LIKE '%hybrid%' THEN 4
                    ELSE 5
                END,
                id DESC
            LIMIT 1
        """, (actual_subtopic_id,)).fetchone()

        processed_data = row_to_dict(processed_row) if processed_row else None

        # Convert markdown to HTML
        raw_html = None
        if content_data.get('markdown_content'):
            md_html = markdown.markdown(
                content_data['markdown_content'],
                extensions=[
                    'markdown.extensions.fenced_code',
                    'markdown.extensions.tables',
                    'markdown.extensions.nl2br',
                    'markdown.extensions.sane_lists',
                    'markdown.extensions.toc',
                    'markdown.extensions.codehilite',
                    'markdown.extensions.footnotes',
                    'markdown.extensions.smarty'
                ]
            )

            # Load CSS if available
            css_path = STATIC_DIR / "markdown_style.css"
            css_style = ""
            if css_path.exists():
                css_style = css_path.read_text(encoding='utf-8')

            raw_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{content_data.get('subtopic_name') or content_data.get('title')}</title>
                <style>
                {css_style}
                .raw-markdown-content {{
                    font-family: Georgia, 'Times New Roman', Times, serif;
                    line-height: 1.8;
                    color: #1a1a1a;
                    padding: 40px 60px;
                    max-width: 900px;
                    margin: 0 auto;
                }}
                </style>
            </head>
            <body>
                <div class="raw-markdown-content">
                {md_html}
                </div>
            </body>
            </html>
            """

        return {
            "subtopic_id": actual_subtopic_id,
            "subtopic_name": content_data.get('subtopic_name') or content_data.get('title'),
            "topic_id": content_data.get('topic_id'),
            "topic_name": content_data.get('topic_name'),
            "raw_content": {
                "markdown": content_data.get('markdown_content'),
                "html": raw_html
            },
            "rewrite": {
                "has_rewrite": processed_data is not None,
                "html": extract_body_content(processed_data.get('html_content')) if processed_data else None,
                "created_at": processed_data.get('processed_at') if processed_data else None,
                "processor_version": processed_data.get('processor_version') if processed_data else None
            }
        }
    finally:
        conn.close()

@app.post("/api/rewrite/{subtopic_id}")
async def trigger_rewrite(subtopic_id: str, request: RewriteRequest = RewriteRequest()):
    """Trigger LLM rewrite for a subtopic."""
    from .creative_rewriter_service import rewrite_subtopic

    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")

    try:
        result = rewrite_subtopic(subtopic_id)
        return {
            "success": True,
            "subtopic_id": subtopic_id,
            "message": "Rewrite generated successfully",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rewrite/status/{subtopic_id}")
async def get_rewrite_status(subtopic_id: str):
    """Check if a subtopic has been processed."""
    conn = get_db_connection()
    try:
        row = conn.execute("""
            SELECT id, processor_version, processed_at
            FROM content_processed
            WHERE subtopic_id = ?
            LIMIT 1
        """, (subtopic_id,)).fetchone()

        if row:
            return {
                "has_rewrite": True,
                "version": row['processor_version'],
                "created_at": row['processed_at']
            }
        else:
            return {"has_rewrite": False}
    finally:
        conn.close()

# ============================================================================
# API Routes - Syllabus (Optional, materials folder dependent)
# ============================================================================

@app.get("/api/syllabuses")
async def get_syllabuses():
    """Get all syllabuses from materials folder."""
    syllabuses = []

    if MATERIALS_DIR.exists():
        for item in sorted(MATERIALS_DIR.iterdir()):
            if item.is_dir() and not item.name.endswith('.json'):
                subjects = [s for s in item.iterdir() if s.is_dir()]

                output_path = MATERIALS_OUTPUT_DIR / item.name
                has_content = output_path.exists() and list(output_path.iterdir())

                syllabuses.append({
                    "id": item.name,
                    "name": item.name.replace('-', ' ').replace('_', ' ').title(),
                    "subject_count": len(subjects),
                    "has_content": has_content
                })

    syllabuses.sort(key=lambda x: (not x['has_content'], x['name']))
    return syllabuses

@app.get("/api/syllabuses/{syllabus_id}/subjects")
async def get_subjects(syllabus_id: str):
    """Get all subjects for a syllabus."""
    subjects = []
    syllabus_path = MATERIALS_DIR / syllabus_id
    output_syllabus_path = MATERIALS_OUTPUT_DIR / syllabus_id

    if syllabus_path.exists():
        for item in sorted(syllabus_path.iterdir()):
            if item.is_dir():
                pdf_count = len([f for f in item.iterdir() if f.suffix == '.pdf'])

                for sub in item.iterdir():
                    if sub.is_dir():
                        pdf_count += len([f for f in sub.iterdir() if f.suffix == '.pdf'])

                output_subject_path = output_syllabus_path / item.name
                has_content = False
                content_files = 0

                if output_subject_path.exists():
                    for f in output_subject_path.rglob('*.md'):
                        if 'content' in f.name and f.stat().st_size > 1024:
                            content_files += 1
                    has_content = content_files > 0

                subjects.append({
                    "id": item.name,
                    "name": item.name,
                    "syllabus_id": syllabus_id,
                    "pdf_count": pdf_count,
                    "has_content": has_content,
                    "content_files": content_files
                })

    subjects.sort(key=lambda x: (not x['has_content'], x['name']))
    return subjects

@app.get("/api/syllabuses/{syllabus_id}/subjects/{subject_id}/topics")
async def get_subject_topics(syllabus_id: str, subject_id: str):
    """Get topics/chapters for a subject."""
    topics = []
    subject_path = MATERIALS_DIR / syllabus_id / subject_id
    output_subject_path = MATERIALS_OUTPUT_DIR / syllabus_id / subject_id

    if subject_path.exists():
        for item in sorted(subject_path.iterdir()):
            if item.is_dir():
                output_topic_path = output_subject_path / item.name
                has_content = (output_topic_path / 'content.md').exists() or \
                             (output_topic_path / 'content_enhanced.md').exists()

                topics.append({
                    "id": item.name,
                    "name": item.name.replace('_', ' ').replace('-', ' '),
                    "syllabus_id": syllabus_id,
                    "subject_id": subject_id,
                    "has_content": has_content
                })

    return topics

# ============================================================================
# Health Check (must be before catchall routes)
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint for orchestrator."""
    return {
        "status": "healthy",
        "service": "ai-materials",
        "version": "2.0.0"
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
            detail="Frontend not built. Run setup_production.bat first."
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
                detail="Frontend not built. Run setup_production.bat first."
            )

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    print("AI Materials FastAPI Server starting...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(settings.PORT),
        reload=settings.DEBUG
    )
