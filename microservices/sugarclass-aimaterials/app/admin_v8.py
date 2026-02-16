"""
V8 Admin API Routes
===================
Admin endpoints for V8 content management.

Replaces old admin.py with V8 architecture support.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path
import sqlite3
import json
import uuid
import os
from datetime import datetime

from .deps import get_current_admin

# ============================================================================
# CONFIGURATION
# ============================================================================

APP_DIR = Path(__file__).parent
DB_PATH = Path(os.getenv("DB_PATH", APP_DIR / "database" / "rag_content.db"))
MARKDOWN_DIR = APP_DIR.parent.parent / "output/markdown"

# Public router - for viewing V8 content (no auth required)
public_router = APIRouter(prefix="/api/v8", tags=["v8-public"])

# Admin router - for generating/managing V8 content (auth required)
admin_router = APIRouter(prefix="/api/admin/v8", tags=["admin-v8"], dependencies=[Depends(get_current_admin)])

# Keep backward compatibility - router alias for existing code
router = admin_router

# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class SubtopicListResponse(BaseModel):
    """Response model for subtopic list"""
    subtopics: List[Dict[str, Any]]
    total: int


class V8ContentStatus(BaseModel):
    """V8 content generation status"""
    subtopic_id: int
    has_concepts: bool
    concept_count: int
    svg_count: int
    quiz_count: int
    flashcard_count: int
    reallife_image_count: int
    processed_at: Optional[str]


class GenerateV8Request(BaseModel):
    """Request to generate V8 content"""
    force_regenerate: bool = False
    generate_svgs: bool = True
    generate_quiz: bool = True
    generate_flashcards: bool = True
    generate_images: bool = False  # Grok images (optional, slow)
    custom_prompt: Optional[str] = None  # Additional user instructions


class TaskResponse(BaseModel):
    """Background task response"""
    task_id: str
    status: str
    message: str


class ConceptUpdateRequest(BaseModel):
    """Update concept request"""
    title: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None


# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================================
# SUBJECT & TOPIC MANAGEMENT
# ============================================================================

@router.get("/subjects")
async def list_subjects():
    """List all subjects"""
    conn = get_db_connection()
    subjects = conn.execute("""
        SELECT
            s.id,
            s.id AS subject_id,
            s.name,
            s.code,
            sy.name AS syllabus_name,
            (SELECT COUNT(*) FROM topics WHERE subject_id = s.id) AS topic_count
        FROM subjects s
        LEFT JOIN syllabuses sy ON s.syllabus_id = sy.id
        ORDER BY sy.name, s.name
    """).fetchall()
    conn.close()

    return {
        "subjects": [dict(row) for row in subjects]
    }


@router.get("/subjects/{subject_id}/topics")
async def list_subject_topics(subject_id: str):
    """List all topics for a subject"""
    conn = get_db_connection()
    topics = conn.execute("""
        SELECT
            t.id,
            t.id AS topic_id,
            t.name,
            t.order_num,
            (SELECT COUNT(*) FROM subtopics WHERE topic_id = t.id) AS subtopic_count,
            (SELECT COUNT(*) FROM subtopics WHERE topic_id = t.id AND processed_at IS NOT NULL) AS processed_count
        FROM topics t
        WHERE t.subject_id = ?
        ORDER BY t.order_num, t.name
    """, (subject_id,)).fetchall()
    conn.close()

    return {
        "topics": [dict(row) for row in topics]
    }


@router.get("/topics/{topic_id}/subtopics")
async def list_topic_subtopics(
    topic_id: str,
    include_status: bool = Query(False)
):
    """List all subtopics for a topic"""
    conn = get_db_connection()

    if include_status:
        subtopics = conn.execute("""
            SELECT
                s.id,
                s.id AS subtopic_id,
                s.name,
                s.order_num,
                s.processed_at,
                COUNT(DISTINCT c.id) AS v8_concepts_count,
                COUNT(DISTINCT q.id) AS quiz_count,
                COUNT(DISTINCT f.id) AS flashcard_count
            FROM subtopics s
            LEFT JOIN v8_concepts c ON s.id = c.subtopic_id
            LEFT JOIN v8_quiz_questions q ON s.id = q.subtopic_id
            LEFT JOIN v8_flashcards f ON s.id = f.subtopic_id
            WHERE s.topic_id = ?
            GROUP BY s.id
            ORDER BY s.order_num
        """, (topic_id,)).fetchall()
    else:
        subtopics = conn.execute("""
            SELECT
                id,
                id AS subtopic_id,
                name,
                order_num,
                processed_at
            FROM subtopics
            WHERE topic_id = ?
            ORDER BY order_num
        """, (topic_id,)).fetchall()

    conn.close()

    return {
        "subtopics": [dict(row) for row in subtopics]
    }


# ============================================================================
# SUBTOPIC MANAGEMENT
# ============================================================================

@router.get("/subtopics/{subtopic_id}")
async def get_subtopic(subtopic_id: str):
    """Get full subtopic details with V8 content"""
    conn = get_db_connection()

    # Get subtopic info
    subtopic = conn.execute("""
        SELECT id, id AS subtopic_id, name, order_num, processed_at
        FROM subtopics WHERE id = ?
    """, (subtopic_id,)).fetchone()

    if not subtopic:
        conn.close()
        raise HTTPException(status_code=404, detail="Subtopic not found")

    subtopic = dict(subtopic)

    # Get learning objectives
    objectives = conn.execute("""
        SELECT objective_text, order_num
        FROM v8_learning_objectives
        WHERE subtopic_id = ?
        ORDER BY order_num
    """, (subtopic_id,)).fetchall()
    subtopic['learning_objectives'] = [dict(row) for row in objectives]

    # Get key terms
    terms = conn.execute("""
        SELECT term, definition, order_num
        FROM v8_key_terms
        WHERE subtopic_id = ?
        ORDER BY order_num
    """, (subtopic_id,)).fetchall()
    subtopic['key_terms'] = [dict(row) for row in terms]

    # Get formulas
    formulas = conn.execute("""
        SELECT formula, description, order_num
        FROM v8_formulas
        WHERE subtopic_id = ?
        ORDER BY order_num
    """, (subtopic_id,)).fetchall()
    subtopic['formulas'] = [dict(row) for row in formulas]

    # Get concepts with generated content
    concepts = conn.execute("""
        SELECT
            c.id,
            c.concept_key,
            c.title,
            c.description,
            c.icon,
            c.order_num,
            GROUP_CONCAT(
                gc.content_type || ':' || gc.content,
                '||'
            ) AS generated_content
        FROM v8_concepts c
        LEFT JOIN v8_generated_content gc ON c.id = gc.concept_id
        WHERE c.subtopic_id = ?
        GROUP BY c.id
        ORDER BY c.order_num
    """, (subtopic_id,)).fetchall()

    concept_list = []
    for row in concepts:
        concept = dict(row)
        # Parse generated content
        generated = {}
        if concept.get('generated_content'):
            for item in concept['generated_content'].split('||'):
                if ':' in item:
                    ctype, ccontent = item.split(':', 1)
                    generated[ctype] = ccontent
        concept['generated'] = generated
        if 'generated_content' in concept:
            del concept['generated_content']
        concept_list.append(concept)

    subtopic['concepts'] = concept_list

    # Get quiz questions
    quiz = conn.execute("""
        SELECT * FROM v8_quiz_questions
        WHERE subtopic_id = ?
        ORDER BY question_num
    """, (subtopic_id,)).fetchall()
    subtopic['quiz'] = [dict(row) for row in quiz]

    # Get flashcards
    flashcards = conn.execute("""
        SELECT * FROM v8_flashcards
        WHERE subtopic_id = ?
        ORDER BY card_num
    """, (subtopic_id,)).fetchall()
    subtopic['flashcards'] = [dict(row) for row in flashcards]

    # Get real-life images
    images = conn.execute("""
        SELECT * FROM v8_reallife_images
        WHERE subtopic_id = ?
        ORDER BY image_type
    """, (subtopic_id,)).fetchall()
    subtopic['reallife_images'] = [dict(row) for row in images]

    conn.close()

    return subtopic


@router.get("/subtopics/{subtopic_id}/status")
async def get_subtopic_status(subtopic_id: str):
    """Get V8 content generation status for a subtopic"""
    conn = get_db_connection()

    # Get subtopic basic info
    subtopic = conn.execute("""
        SELECT id, processed_at FROM subtopics WHERE id = ?
    """, (subtopic_id,)).fetchone()

    if not subtopic:
        conn.close()
        raise HTTPException(status_code=404, detail="Subtopic not found")

    # Get content counts
    concept_count = conn.execute(
        "SELECT COUNT(*) as count FROM v8_concepts WHERE subtopic_id = ?",
        (subtopic_id,)
    ).fetchone()['count']

    svg_count = conn.execute(
        "SELECT COUNT(*) as count FROM v8_generated_content gc JOIN v8_concepts c ON gc.concept_id = c.id WHERE c.subtopic_id = ? AND gc.content_type = 'svg'",
        (subtopic_id,)
    ).fetchone()['count']

    quiz_count = conn.execute(
        "SELECT COUNT(*) as count FROM v8_quiz_questions WHERE subtopic_id = ?",
        (subtopic_id,)
    ).fetchone()['count']

    flashcard_count = conn.execute(
        "SELECT COUNT(*) as count FROM v8_flashcards WHERE subtopic_id = ?",
        (subtopic_id,)
    ).fetchone()['count']

    reallife_image_count = conn.execute(
        "SELECT COUNT(*) as count FROM v8_reallife_images WHERE subtopic_id = ?",
        (subtopic_id,)
    ).fetchone()['count']

    conn.close()

    return {
        "subtopic_id": subtopic_id,
        "has_concepts": concept_count > 0,
        "concept_count": concept_count,
        "svg_count": svg_count,
        "quiz_count": quiz_count,
        "flashcard_count": flashcard_count,
        "reallife_image_count": reallife_image_count,
        "processed_at": subtopic['processed_at']
    }


# ============================================================================
# V8 CONTENT GENERATION
# ============================================================================

@router.post("/subtopics/{subtopic_id}/generate")
async def generate_v8_content(
    subtopic_id: str,
    request: GenerateV8Request,
    background_tasks: BackgroundTasks
):
    """Generate V8 content for a subtopic (background task)"""

    # Check if subtopic exists
    conn = get_db_connection()
    subtopic = conn.execute("SELECT * FROM subtopics WHERE id = ?", (subtopic_id,)).fetchone()
    conn.close()

    if not subtopic:
        raise HTTPException(status_code=404, detail="Subtopic not found")

    # Check if already generated
    if not request.force_regenerate:
        conn = get_db_connection()
        existing = conn.execute("""
            SELECT COUNT(*) as count FROM v8_concepts WHERE subtopic_id = ?
        """, (subtopic_id,)).fetchone()
        conn.close()

        if existing['count'] > 0:
            return {
                "task_id": "",
                "status": "already_generated",
                "message": "V8 content already exists. Use force_regenerate=true to regenerate."
            }

    # Create background task
    task_id = str(uuid.uuid4())

    # Initialize task in database
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO v8_processing_tasks (task_id, subtopic_id, task_type, status, progress, message)
        VALUES (?, ?, 'full_generation', 'pending', 0, 'Task created')
    """, (task_id, subtopic_id))
    conn.commit()
    conn.close()

    # Add background task
    background_tasks.add_task(
        run_v8_generation_task,
        task_id,
        subtopic_id,
        request.dict() if hasattr(request, 'dict') else dict(request)
    )

    return {
        "task_id": task_id,
        "status": "pending",
        "message": "V8 content generation started"
    }


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get background task status"""
    conn = get_db_connection()

    task = conn.execute("""
        SELECT * FROM v8_processing_tasks WHERE task_id = ?
    """, (task_id,)).fetchone()

    if not task:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    # Get logs
    logs = conn.execute("""
        SELECT log_level, message, created_at
        FROM v8_task_logs
        WHERE task_id = ?
        ORDER BY created_at DESC
        LIMIT 50
    """, (task_id,)).fetchall()

    conn.close()

    return {
        "task_id": task['task_id'],
        "status": task['status'],
        "progress": task['progress'],
        "message": task['message'],
        "error": task['error'],
        "started_at": task['started_at'],
        "completed_at": task['completed_at'],
        "logs": [dict(row) for row in logs]
    }


# ============================================================================
# CONCEPT MANAGEMENT
# ============================================================================

@router.put("/concepts/{concept_id}")
async def update_concept(concept_id: int, request: ConceptUpdateRequest):
    """Update a concept"""
    conn = get_db_connection()

    # Build update query dynamically
    updates = []
    params = []

    if request.title is not None:
        updates.append("title = ?")
        params.append(request.title)

    if request.description is not None:
        updates.append("description = ?")
        params.append(request.description)

    if request.icon is not None:
        updates.append("icon = ?")
        params.append(request.icon)

    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(concept_id)

    query = f"UPDATE v8_concepts SET {', '.join(updates)} WHERE id = ?"
    conn.execute(query, params)
    conn.commit()
    conn.close()

    return {"message": "Concept updated successfully"}


@router.post("/concepts/{concept_id}/regenerate-svg")
async def regenerate_concept_svg(
    concept_id: int,
    background_tasks: BackgroundTasks
):
    """Regenerate SVG for a concept"""
    # Get concept info
    conn = get_db_connection()
    concept = conn.execute("""
        SELECT c.*, s.name AS subtopic_name
        FROM v8_concepts c
        JOIN subtopics s ON c.subtopic_id = s.id
        WHERE c.id = ?
    """, (concept_id,)).fetchone()
    conn.close()

    if not concept:
        raise HTTPException(status_code=404, detail="Concept not found")

    # Create background task
    task_id = str(uuid.uuid4())

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO v8_processing_tasks (task_id, subtopic_id, task_type, status, message)
        VALUES (?, ?, 'svg_regenerate', 'pending', ?)
    """, (task_id, concept['subtopic_id'], f"Regenerating SVG for {concept['title']}"))
    conn.commit()
    conn.close()

    background_tasks.add_task(
        run_svg_regeneration,
        task_id,
        concept_id,
        dict(concept)
    )

    return TaskResponse(
        task_id=task_id,
        status="pending",
        message="SVG regeneration started"
    )


# ============================================================================
# QUIZ MANAGEMENT
# ============================================================================

@router.put("/quiz/{question_id}")
async def update_quiz_question(
    question_id: int,
    question_text: Optional[str] = None,
    options: Optional[Dict[str, str]] = None,
    correct_answer: Optional[str] = None,
    explanation: Optional[str] = None
):
    """Update a quiz question"""
    conn = get_db_connection()

    updates = []
    params = []

    if question_text is not None:
        updates.append("question_text = ?")
        params.append(question_text)

    if options is not None:
        updates.append("options = ?")
        params.append(json.dumps(options))

    if correct_answer is not None:
        updates.append("correct_answer = ?")
        params.append(correct_answer)

    if explanation is not None:
        updates.append("explanation = ?")
        params.append(explanation)

    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(question_id)

    query = f"UPDATE v8_quiz_questions SET {', '.join(updates)} WHERE id = ?"
    conn.execute(query, params)
    conn.commit()
    conn.close()

    return {"message": "Question updated successfully"}


# ============================================================================
# BACKGROUND TASK FUNCTIONS
# ============================================================================

def run_v8_generation_task(task_id: str, subtopic_id: str, options: Dict):
    """Background task to generate V8 content"""

    def update_task(status: str, progress: int, message: str, error: str = None):
        conn = get_db_connection()
        conn.execute("""
            UPDATE v8_processing_tasks
            SET status = ?, progress = ?, message = ?, error = ?, started_at = COALESCE(started_at, CURRENT_TIMESTAMP)
            WHERE task_id = ?
        """, (status, progress, message, error, task_id))
        conn.commit()

        if status in ['completed', 'failed']:
            conn.execute("""
                UPDATE v8_processing_tasks SET completed_at = CURRENT_TIMESTAMP WHERE task_id = ?
            """, (task_id,))
            conn.commit()

        conn.close()

    def add_log(level: str, message: str):
        conn = get_db_connection()
        conn.execute("""
            INSERT INTO v8_task_logs (task_id, log_level, message)
            VALUES (?, ?, ?)
        """, (task_id, level, message))
        conn.commit()
        conn.close()

    try:
        # Import here to avoid circular imports
        from .processors.content_processor_v8 import V8Processor, GeminiClient

        add_log('info', f"Starting V8 generation for subtopic {subtopic_id}")
        update_task('running', 10, 'Initializing...')

        # Load subtopic data
        conn = get_db_connection()
        subtopic = conn.execute("""
            SELECT s.*, t.name AS topic_name
            FROM subtopics s
            JOIN topics t ON s.topic_id = t.id
            WHERE s.id = ?
        """, (subtopic_id,)).fetchone()

        if not subtopic:
            raise Exception(f"Subtopic {subtopic_id} not found")

        subtopic = dict(subtopic)

        # Read markdown content - try content_raw table first, then file
        markdown_content = None

        # Option 1: Try content_raw table
        raw_content = conn.execute("""
            SELECT markdown_content FROM content_raw
            WHERE subtopic_id = ?
            ORDER BY id DESC LIMIT 1
        """, (subtopic_id,)).fetchone()

        if raw_content and raw_content['markdown_content']:
            markdown_content = raw_content['markdown_content']
            add_log('info', "Loaded content from content_raw table")

        # Option 2: Try markdown file path
        if not markdown_content:
            markdown_path = Path(subtopic['markdown_file_path']) if subtopic.get('markdown_file_path') else None
            if markdown_path and markdown_path.exists():
                with open(markdown_path, 'r', encoding='utf-8', errors='ignore') as f:
                    markdown_content = f.read()
                add_log('info', f"Loaded content from file: {markdown_path.name}")

        if not markdown_content:
            raise Exception(f"No content found for subtopic {subtopic_id}. Neither content_raw nor markdown file exists.")

        conn.close()

        add_log('info', f"Loaded markdown: {len(markdown_content)} chars")
        update_task('running', 20, 'Analyzing structure...')

        # Initialize generator
        processor = V8Processor()

        # Check if API is configured
        if not processor.gemini:
            raise Exception("LLM API key not configured. Set LLM_API_KEY or GEMINI_API_KEY environment variable.")

        # Analyze structure
        concepts = processor.gemini.analyze_structure(markdown_content)

        if not concepts:
            concepts = processor.generator._get_fallback_concepts(subtopic['name'])

        add_log('info', f"Identified {len(concepts)} concepts")
        update_task('running', 30, f'Found {len(concepts)} concepts')

        # Save concepts (clear existing first)
        conn = get_db_connection()
        conn.execute("DELETE FROM v8_concepts WHERE subtopic_id = ?", (subtopic_id,))
        conn.execute("DELETE FROM v8_generated_content WHERE concept_id IN (SELECT id FROM v8_concepts WHERE subtopic_id = ?)", (subtopic_id,))
        conn.commit()
        conn.close()

        from .processors.content_processor_v8 import ConceptData
        for i, concept_data in enumerate(concepts):
            concept = ConceptData(
                concept_key=concept_data.get('id', f'concept_{i}'),
                title=concept_data.get('title', 'Concept'),
                description=concept_data.get('description', ''),
                icon=concept_data.get('icon', '📚'),
                order_num=i
            )
            processor.db.save_concepts(subtopic_id, [concept])

        add_log('info', "Saved concepts to database")
        update_task('running', 40, 'Generating SVGs and content...')

        # Get saved concepts
        saved_concepts = processor.db.get_concepts(subtopic_id)

        # Generate SVGs and bullets
        for i, concept in enumerate(saved_concepts):
            add_log('info', f"Generating SVG for: {concept['title']}")

            svg = processor.gemini.generate_svg(concept['title'], concept['description'])
            if svg:
                processor.db.update_generated_content(concept['id'], 'svg', svg)
                add_log('info', f"✓ SVG generated for {concept['title']}")

            bullets = processor.gemini.generate_bullets(
                concept['title'],
                concept['description'],
                markdown_content
            )
            if bullets:
                processor.db.update_generated_content(concept['id'], 'bullets', bullets)
                add_log('info', f"✓ Bullets generated for {concept['title']}")

            progress = 40 + int(40 * (i + 1) / len(saved_concepts))
            update_task('running', progress, f'Processing concept {i+1}/{len(saved_concepts)}')

        # Generate quiz
        if options.get('generate_quiz', True):
            add_log('info', "Generating quiz...")
            update_task('running', 85, 'Generating quiz...')

            conn = get_db_connection()
            conn.execute("DELETE FROM v8_quiz_questions WHERE subtopic_id = ?", (subtopic_id,))
            conn.commit()
            conn.close()

            quiz = processor.gemini.generate_quiz(subtopic['name'], markdown_content, 5)
            if quiz and quiz.get('questions'):
                for i, q in enumerate(quiz['questions'], 1):
                    processor.db.save_quiz_question(subtopic_id, i, q)
                add_log('info', f"✓ Generated {len(quiz['questions'])} quiz questions")

        # Generate flashcards
        if options.get('generate_flashcards', True):
            add_log('info', "Generating flashcards...")
            update_task('running', 90, 'Generating flashcards...')

            conn = get_db_connection()
            conn.execute("DELETE FROM v8_flashcards WHERE subtopic_id = ?", (subtopic_id,))
            conn.commit()
            conn.close()

            flashcards = processor.gemini.generate_flashcards(subtopic['name'], markdown_content, 8)
            if flashcards and flashcards.get('cards'):
                for i, card in enumerate(flashcards['cards'], 1):
                    processor.db.save_flashcard(subtopic_id, i, card.get('front', ''), card.get('back', ''))
                add_log('info', f"✓ Generated {len(flashcards['cards'])} flashcards")

        # Mark as processed
        processor.db.mark_subtopic_processed(subtopic_id)

        add_log('info', "V8 generation complete!")
        update_task('completed', 100, 'V8 content generation complete!')

        processor.close()

    except Exception as e:
        import traceback
        error_msg = str(e)
        add_log('error', error_msg)
        add_log('error', traceback.format_exc())
        update_task('failed', 0, 'Generation failed', error_msg)


def run_svg_regeneration(task_id: str, concept_id: int, concept: Dict):
    """Background task to regenerate SVG"""

    def update_task(status: str, message: str):
        conn = get_db_connection()
        conn.execute("""
            UPDATE v8_processing_tasks
            SET status = ?, message = ?, started_at = COALESCE(started_at, CURRENT_TIMESTAMP)
            WHERE task_id = ?
        """, (status, message, task_id))
        conn.commit()
        conn.close()

    try:
        from .processors.content_processor_v8 import V8Processor

        update_task('running', 'Regenerating SVG...')

        processor = V8Processor()

        svg = processor.gemini.generate_svg(concept['title'], concept['description'])

        if svg:
            processor.db.update_generated_content(concept_id, 'svg', svg)
            update_task('completed', 'SVG regenerated successfully')
        else:
            update_task('failed', 'Failed to regenerate SVG')

        processor.close()

    except Exception as e:
        update_task('failed', f'Error: {str(e)}')


# ============================================================================
# PUBLIC ROUTES - No authentication required (for viewing content)
# ============================================================================

@public_router.get("/subjects")
async def public_get_subjects():
    """Get all subjects with V8 content - public endpoint"""
    conn = get_db_connection()

    subjects = conn.execute("""
        SELECT s.id, s.id AS subject_id, s.name, s.code,
               COUNT(DISTINCT t.id) as topic_count,
               COUNT(DISTINCT sub.id) as subtopic_count,
               COUNT(DISTINCT CASE WHEN sub.processed_at IS NOT NULL THEN sub.id END) as processed_count
        FROM subjects s
        LEFT JOIN topics t ON t.subject_id = s.id
        LEFT JOIN subtopics sub ON sub.topic_id = t.id
        GROUP BY s.id
        HAVING processed_count > 0
        ORDER BY s.name
    """).fetchall()

    conn.close()
    return {"subjects": [dict(row) for row in subjects]}


@public_router.get("/subjects/{subject_id}/topics")
async def public_get_subject_topics(subject_id: str):
    """Get topics for a subject - public endpoint"""
    conn = get_db_connection()

    topics = conn.execute("""
        SELECT t.id, t.id AS topic_id, t.name, t.order_num,
               COUNT(DISTINCT s.id) as subtopic_count,
               COUNT(DISTINCT CASE WHEN s.processed_at IS NOT NULL THEN s.id END) as processed_count
        FROM topics t
        LEFT JOIN subtopics s ON s.topic_id = t.id
        WHERE t.subject_id = ?
        GROUP BY t.id
        HAVING processed_count > 0
        ORDER BY t.order_num
    """, (subject_id,)).fetchall()

    conn.close()
    return {"topics": [dict(row) for row in topics]}


@public_router.get("/topics/{topic_id}/subtopics")
async def public_get_topic_subtopics(topic_id: str, include_status: bool = True):
    """Get subtopics for a topic - public endpoint"""
    conn = get_db_connection()

    subtopics = conn.execute("""
        SELECT s.id, s.id AS subtopic_id, s.name, s.order_num, s.processed_at
        FROM subtopics s
        WHERE s.topic_id = ? AND s.processed_at IS NOT NULL
        ORDER BY s.order_num
    """, (topic_id,)).fetchall()

    result = []
    for row in subtopics:
        sub = dict(row)
        if include_status:
            # Get V8 content counts
            sub['v8_concepts_count'] = conn.execute(
                "SELECT COUNT(*) FROM v8_concepts WHERE subtopic_id = ?",
                (row['id'],)
            ).fetchone()[0]
            sub['quiz_count'] = conn.execute(
                "SELECT COUNT(*) FROM v8_quiz_questions WHERE subtopic_id = ?",
                (row['id'],)
            ).fetchone()[0]
            sub['flashcard_count'] = conn.execute(
                "SELECT COUNT(*) FROM v8_flashcards WHERE subtopic_id = ?",
                (row['id'],)
            ).fetchone()[0]
        result.append(sub)

    conn.close()
    return {"subtopics": result, "total": len(result)}


@public_router.get("/subtopics/{subtopic_id}")
async def public_get_subtopic_content(subtopic_id: str):
    """Get V8 content for a subtopic - public endpoint"""
    conn = get_db_connection()

    # Get subtopic info
    subtopic = conn.execute("""
        SELECT id, name FROM subtopics WHERE id = ?
    """, (subtopic_id,)).fetchone()

    if not subtopic:
        conn.close()
        raise HTTPException(status_code=404, detail="Subtopic not found")

    # Get concepts with generated content
    concepts = conn.execute("""
        SELECT c.id, c.concept_key, c.title, c.description, c.icon, c.order_num
        FROM v8_concepts c
        WHERE c.subtopic_id = ?
        ORDER BY c.order_num
    """, (subtopic_id,)).fetchall()

    concept_list = []
    for concept in concepts:
        c = dict(concept)
        # Get generated content for this concept
        content_rows = conn.execute("""
            SELECT content_type, content FROM v8_generated_content
            WHERE concept_id = ?
        """, (c['id'],)).fetchall()

        generated = {}
        for row in content_rows:
            generated[row['content_type']] = row['content']
        c['generated'] = generated
        concept_list.append(c)

    # Get quiz questions
    quiz = conn.execute("""
        SELECT id, question_num, question_text, options, correct_answer, explanation, difficulty
        FROM v8_quiz_questions
        WHERE subtopic_id = ?
        ORDER BY question_num
    """, (subtopic_id,)).fetchall()

    # Get flashcards
    flashcards = conn.execute("""
        SELECT id, card_num, front, back
        FROM v8_flashcards
        WHERE subtopic_id = ?
        ORDER BY card_num
    """, (subtopic_id,)).fetchall()

    conn.close()

    return {
        "subtopic_id": subtopic_id,
        "name": subtopic['name'],
        "concepts": concept_list,
        "quiz": [dict(q) for q in quiz],
        "flashcards": [dict(f) for f in flashcards]
    }


@public_router.get("/subtopics/{subtopic_id}/status")
async def public_get_subtopic_status(subtopic_id: str):
    """Get V8 content status for a subtopic - public endpoint"""
    conn = get_db_connection()

    # Get subtopic basic info
    subtopic = conn.execute("""
        SELECT id, processed_at FROM subtopics WHERE id = ?
    """, (subtopic_id,)).fetchone()

    if not subtopic:
        conn.close()
        raise HTTPException(status_code=404, detail="Subtopic not found")

    # Get content counts
    concept_count = conn.execute(
        "SELECT COUNT(*) as count FROM v8_concepts WHERE subtopic_id = ?",
        (subtopic_id,)
    ).fetchone()['count']

    svg_count = conn.execute(
        "SELECT COUNT(*) as count FROM v8_generated_content gc JOIN v8_concepts c ON gc.concept_id = c.id WHERE c.subtopic_id = ? AND gc.content_type = 'svg'",
        (subtopic_id,)
    ).fetchone()['count']

    quiz_count = conn.execute(
        "SELECT COUNT(*) as count FROM v8_quiz_questions WHERE subtopic_id = ?",
        (subtopic_id,)
    ).fetchone()['count']

    flashcard_count = conn.execute(
        "SELECT COUNT(*) as count FROM v8_flashcards WHERE subtopic_id = ?",
        (subtopic_id,)
    ).fetchone()['count']

    conn.close()

    return {
        "subtopic_id": subtopic_id,
        "has_concepts": concept_count > 0,
        "concept_count": concept_count,
        "svg_count": svg_count,
        "quiz_count": quiz_count,
        "flashcard_count": flashcard_count,
        "processed_at": subtopic['processed_at']
    }
