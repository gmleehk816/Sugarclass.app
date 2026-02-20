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
import re
import shutil
import sqlite3
import json
import uuid
import os
import time
import hashlib
import threading
from datetime import datetime

# ============================================================================
# CANCEL EVENT REGISTRY
# Maps task_id -> threading.Event so cancel_task() can wake sleeping workers
# instantly without waiting for the next DB poll.
# ============================================================================
_cancel_events: Dict[str, threading.Event] = {}

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
    past_paper_count: int
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


class V8IngestRequest(BaseModel):
    """Request to ingest a markdown file with V8 pipeline"""
    batch_id: str
    filename: str
    subject_name: str
    syllabus: str = "IGCSE"
    target_subject_id: Optional[str] = None
    exam_board: Optional[str] = None   # e.g. "CIE Chemistry (0620)", "AQA Biology (7402)"
    ib_level: Optional[str] = None     # "SL" or "HL" for IB subjects


class ConceptUpdateRequest(BaseModel):
    """Update concept request"""
    title: Optional[str] = None
    description: Optional[str] = None
    bullets: Optional[str] = None
    icon: Optional[str] = None


class SubtopicUpdateRequest(BaseModel):
    """Update subtopic request"""
    name: Optional[str] = None
    order_num: Optional[int] = None


class TopicUpdateRequest(BaseModel):
    """Update topic request"""
    name: Optional[str] = None
    order_num: Optional[int] = None


class SubjectRenameRequest(BaseModel):
    """Rename subject request"""
    name: str


class SVGRegenerateRequest(BaseModel):
    """SVG regeneration request"""
    prompt: Optional[str] = None


class QuizQuestionUpdateRequest(BaseModel):
    """Update quiz question request"""
    question_text: Optional[str] = None
    options: Optional[Dict[str, str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None


class FlashcardUpdateRequest(BaseModel):
    """Update flashcard request"""
    front: Optional[str] = None
    back: Optional[str] = None


class RealLifeImageUpdateRequest(BaseModel):
    """Update real-life image request"""
    title: Optional[str] = None
    description: Optional[str] = None
    image_type: Optional[str] = None


class PastPaperCreateRequest(BaseModel):
    """Create a past paper request"""
    question_text: str
    marks: int = 1
    year: Optional[str] = None
    season: Optional[str] = None
    paper_reference: Optional[str] = None
    mark_scheme: Optional[str] = None


class PastPaperUpdateRequest(BaseModel):
    """Update a past paper request"""
    question_text: Optional[str] = None
    marks: Optional[int] = None
    year: Optional[str] = None
    season: Optional[str] = None
    paper_reference: Optional[str] = None
    mark_scheme: Optional[str] = None


class SubjectListResponse(BaseModel):
    """List subjects response"""
    subjects: List[Dict[str, Any]]


# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ============================================================================
# SUBJECT & TOPIC MANAGEMENT
# ============================================================================

@router.delete("/subjects/{subject_id}")
async def delete_subject(subject_id: int):
    """Recursively delete a subject and all its topics/subtopics (cascading)"""
    conn = get_db_connection()
    try:
        # Check if subject exists
        subject = conn.execute("SELECT id FROM subjects WHERE id = ?", (subject_id,)).fetchone()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")

        # Delete subject (cascading will handle topics, subtopics, and content)
        conn.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
        conn.commit()
        return {"success": True, "message": f"Subject {subject_id} deleted successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete subject: {str(e)}")
    finally:
        conn.close()


@router.patch("/subjects/{subject_id}")
async def rename_subject(subject_id: int, request: SubjectRenameRequest):
    """Rename a subject"""
    conn = get_db_connection()
    try:
        # Check if subject exists
        subject = conn.execute("SELECT name FROM subjects WHERE id = ?", (subject_id,)).fetchone()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")

        conn.execute("UPDATE subjects SET name = ? WHERE id = ?", (request.name, subject_id))
        conn.commit()
        return {"success": True, "message": f"Subject {subject_id} renamed to {request.name}"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to rename subject: {str(e)}")
    finally:
        conn.close()


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
                COUNT(DISTINCT f.id) AS flashcard_count,
                COUNT(DISTINCT p.id) AS past_paper_count
            FROM subtopics s
            LEFT JOIN v8_concepts c ON s.id = c.subtopic_id
            LEFT JOIN v8_quiz_questions q ON s.id = q.subtopic_id
            LEFT JOIN v8_flashcards f ON s.id = f.subtopic_id
            LEFT JOIN v8_past_papers p ON s.id = p.subtopic_id
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


@router.delete("/topics/{topic_id}")
async def delete_topic(topic_id: str):
    """Delete a topic and all its subtopics (cascading)"""
    conn = get_db_connection()
    try:
        # Check if topic exists
        topic = conn.execute("SELECT id FROM topics WHERE id = ?", (topic_id,)).fetchone()
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        # Delete topic (cascading will handle subtopics and content)
        conn.execute("DELETE FROM topics WHERE id = ?", (topic_id,))
        conn.commit()
        return {"success": True, "message": f"Topic {topic_id} deleted successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete topic: {str(e)}")
    finally:
        conn.close()


@router.patch("/topics/{topic_id}")
async def update_topic(topic_id: str, request: TopicUpdateRequest):
    """Update a topic (rename or reorder)"""
    conn = get_db_connection()
    try:
        # Check if topic exists
        topic = conn.execute("SELECT name FROM topics WHERE id = ?", (topic_id,)).fetchone()
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")

        updates = []
        params = []
        if request.name is not None:
            updates.append("name = ?")
            params.append(request.name)
        if request.order_num is not None:
            updates.append("order_num = ?")
            params.append(request.order_num)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        params.append(topic_id)
        conn.execute(f"UPDATE topics SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        return {"success": True, "message": f"Topic {topic_id} updated successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update topic: {str(e)}")
    finally:
        conn.close()


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
    
    quiz_list = []
    for row in quiz:
        q = dict(row)
        if q.get('options'):
            try:
                q['options'] = json.loads(q['options'])
            except:
                pass
        quiz_list.append(q)
    subtopic['quiz'] = quiz_list

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

    # Get past papers
    past_papers = conn.execute("""
        SELECT * FROM v8_past_papers
        WHERE subtopic_id = ?
        ORDER BY created_at
    """, (subtopic_id,)).fetchall()
    subtopic['past_papers'] = [dict(row) for row in past_papers]

    conn.close()

    return subtopic


@router.delete("/subtopics/{subtopic_id}")
async def delete_subtopic(subtopic_id: str):
    """Delete a subtopic and all its content (cascading)"""
    conn = get_db_connection()
    try:
        # Check if subtopic exists
        subtopic = conn.execute("SELECT id FROM subtopics WHERE id = ?", (subtopic_id,)).fetchone()
        if not subtopic:
            raise HTTPException(status_code=404, detail="Subtopic not found")

        # Delete subtopic (cascading will handle v8 content tables)
        conn.execute("DELETE FROM subtopics WHERE id = ?", (subtopic_id,))
        conn.commit()
        return {"success": True, "message": f"Subtopic {subtopic_id} deleted successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete subtopic: {str(e)}")
    finally:
        conn.close()


@router.patch("/subtopics/{subtopic_id}")
async def update_subtopic(subtopic_id: str, request: SubtopicUpdateRequest):
    """Update a subtopic (rename or reorder)"""
    conn = get_db_connection()
    try:
        # Check if subtopic exists
        subtopic = conn.execute("SELECT name FROM subtopics WHERE id = ?", (subtopic_id,)).fetchone()
        if not subtopic:
            raise HTTPException(status_code=404, detail="Subtopic not found")

        updates = []
        params = []
        if request.name is not None:
            updates.append("name = ?")
            params.append(request.name)
            # Update slug if name changes
            slug = re.sub(r'[^\w\s-]', '', request.name).strip().lower()
            slug = re.sub(r'[-\s]+', '-', slug)
            updates.append("slug = ?")
            params.append(slug)
        if request.order_num is not None:
            updates.append("order_num = ?")
            params.append(request.order_num)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        params.append(subtopic_id)
        conn.execute(f"UPDATE subtopics SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        return {"success": True, "message": f"Subtopic {subtopic_id} updated successfully"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update subtopic: {str(e)}")
    finally:
        conn.close()


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

    past_paper_count = conn.execute(
        "SELECT COUNT(*) as count FROM v8_past_papers WHERE subtopic_id = ?",
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
        "past_paper_count": past_paper_count,
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
    ensure_v8_tables()
    ensure_v8_task_columns()
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


@router.get("/tasks")
async def list_tasks(
    only_active: bool = Query(False),
    task_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=200),
):
    """List V8 background tasks."""
    ensure_v8_tables()
    ensure_v8_task_columns()
    conn = get_db_connection()
    try:
        clauses = []
        params: List[Any] = []
        if only_active:
            clauses.append("status IN ('pending', 'running', 'cancelling')")
        if task_type:
            clauses.append("task_type = ?")
            params.append(task_type)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = conn.execute(f"""
            SELECT task_id, subtopic_id, task_type, status, progress, message, error, started_at, completed_at, created_at
            FROM v8_processing_tasks
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ?
        """, (*params, limit)).fetchall()
        return {"tasks": [dict(r) for r in rows]}
    finally:
        conn.close()


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get background task status"""
    ensure_v8_tables()
    ensure_v8_task_columns()
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
        "task_type": task['task_type'],
        "cancel_requested": bool(task['cancel_requested']) if 'cancel_requested' in task.keys() else False,
        "started_at": task['started_at'],
        "completed_at": task['completed_at'],
        "logs": [dict(row) for row in logs]
    }


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Request cancellation for a running/pending V8 task."""
    ensure_v8_tables()
    ensure_v8_task_columns()
    conn = get_db_connection()
    try:
        task = conn.execute("""
            SELECT task_id, status, task_type
            FROM v8_processing_tasks
            WHERE task_id = ?
        """, (task_id,)).fetchone()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        current_status = (task["status"] or "").lower()
        if current_status in ("completed", "failed", "cancelled"):
            return {"task_id": task_id, "status": current_status, "message": "Task already finished"}

        if current_status == "pending":
            # Pending tasks can be cancelled immediately; they have not begun work yet.
            conn.execute("""
                UPDATE v8_processing_tasks
                SET cancel_requested = 1,
                    status = 'cancelled',
                    message = 'Task cancelled before start',
                    started_at = COALESCE(started_at, CURRENT_TIMESTAMP),
                    cancelled_at = COALESCE(cancelled_at, CURRENT_TIMESTAMP),
                    completed_at = COALESCE(completed_at, CURRENT_TIMESTAMP)
                WHERE task_id = ?
            """, (task_id,))
            conn.execute("""
                INSERT INTO v8_task_logs (task_id, log_level, message)
                VALUES (?, 'warning', ?)
            """, (task_id, "Task cancelled before start"))
            conn.commit()
            return {"task_id": task_id, "status": "cancelled", "message": "Task cancelled before start"}

        conn.execute("""
            UPDATE v8_processing_tasks
            SET cancel_requested = 1,
                status = CASE WHEN status IN ('running', 'pending') THEN 'cancelling' ELSE status END,
                message = 'Cancellation requested by user'
            WHERE task_id = ?
        """, (task_id,))
        conn.execute("""
            INSERT INTO v8_task_logs (task_id, log_level, message)
            VALUES (?, 'warning', ?)
        """, (task_id, "Cancellation requested by user"))
        conn.commit()

        # Signal the worker thread immediately so it wakes from any sleep
        event = _cancel_events.get(task_id)
        if event:
            event.set()

        return {"task_id": task_id, "status": "cancelling", "message": "Cancellation requested"}
    finally:
        conn.close()


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

    if not updates and request.bullets is None:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(concept_id)

    if updates:
        query = f"UPDATE v8_concepts SET {', '.join(updates)} WHERE id = ?"
        conn.execute(query, params)
    
    # Handle bullets update in generated content table
    if request.bullets is not None:
        # Check if record exists
        existing = conn.execute("""
            SELECT id FROM v8_generated_content 
            WHERE concept_id = ? AND content_type = 'bullets'
        """, (concept_id,)).fetchone()
        
        if existing:
            conn.execute("""
                UPDATE v8_generated_content SET content = ? 
                WHERE id = ?
            """, (request.bullets, existing['id']))
        else:
            conn.execute("""
                INSERT INTO v8_generated_content (concept_id, content_type, content)
                VALUES (?, 'bullets', ?)
            """, (concept_id, request.bullets))
            
    conn.commit()
    conn.close()

    return {"message": "Concept updated successfully"}


@router.post("/concepts/{concept_id}/regenerate-svg")
async def regenerate_concept_svg(
    concept_id: int,
    request: SVGRegenerateRequest,
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
        dict(concept),
        request.prompt
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
    request: QuizQuestionUpdateRequest
):
    """Update a quiz question"""
    conn = get_db_connection()

    updates = []
    params = []

    if request.question_text is not None:
        updates.append("question_text = ?")
        params.append(request.question_text)

    if request.options is not None:
        updates.append("options = ?")
        params.append(json.dumps(request.options))

    if request.correct_answer is not None:
        updates.append("correct_answer = ?")
        params.append(request.correct_answer)

    if request.explanation is not None:
        updates.append("explanation = ?")
        params.append(request.explanation)

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
# FLASHCARD MANAGEMENT
# ============================================================================

@router.put("/flashcards/{card_id}")
async def update_flashcard(
    card_id: int,
    request: FlashcardUpdateRequest
):
    """Update a flashcard"""
    conn = get_db_connection()

    updates = []
    params = []

    if request.front is not None:
        updates.append("front = ?")
        params.append(request.front)

    if request.back is not None:
        updates.append("back = ?")
        params.append(request.back)

    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(card_id)

    query = f"UPDATE v8_flashcards SET {', '.join(updates)} WHERE id = ?"
    conn.execute(query, params)
    conn.commit()
    conn.close()

    return {"message": "Flashcard updated successfully"}


# ============================================================================
# REAL LIFE IMAGE MANAGEMENT
# ============================================================================

@router.put("/reallife_images/{image_id}")
async def update_reallife_image(
    image_id: int,
    request: RealLifeImageUpdateRequest
):
    """Update a real-life image record"""
    conn = get_db_connection()

    updates = []
    params = []

    if request.title is not None:
        updates.append("title = ?")
        params.append(request.title)

    if request.description is not None:
        updates.append("description = ?")
        params.append(request.description)

    if request.image_type is not None:
        updates.append("image_type = ?")
        params.append(request.image_type)

    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")

    params.append(image_id)

    query = f"UPDATE v8_reallife_images SET {', '.join(updates)} WHERE id = ?"
    conn.execute(query, params)
    conn.commit()
    conn.close()

    return {"message": "Real-life image updated successfully"}


# ============================================================================
# CHUNK EDITOR — REGENERATION & IMAGE GENERATION
# ============================================================================

class ChunkRegenerateRequest(BaseModel):
    """Request model for regenerating a specific chunk."""
    content: str
    type: str
    focus: Optional[str] = None
    temperature: Optional[float] = 0.7
    subtopic_name: Optional[str] = None
    surrounding_context: Optional[Dict[str, str]] = None  # { "before": "...", "after": "..." }

# Type-specific prompt strategies
CHUNK_TYPE_PROMPTS = {
    "heading": "Rephrase this heading to be more engaging and clear while keeping the same topic scope. Return only the heading HTML tag (e.g. <h2>...</h2>).",
    "text": "Enhance this educational paragraph. Improve clarity, add transition sentences, use active voice, and make it engaging for students. Return only the enhanced HTML paragraph(s).",
    "list": "Improve these list items. Make each point clearer, more specific, and educational. Keep the list structure (<ul>/<ol> with <li> items). Return only the enhanced list HTML.",
    "quote": "Enhance this quote or callout. Make it more impactful and thought-provoking while preserving the core message. Return only the enhanced HTML.",
    "callout": "Improve this callout/details section. Make the content clearer and more helpful for students. Return only the enhanced HTML.",
    "table": "Improve this table's content. Make headers clearer, data more meaningful, and add context where helpful. Return only the enhanced HTML table.",
}


@router.post("/contents/regenerate-chunk", response_model=Dict[str, Any])
async def regenerate_chunk(request: ChunkRegenerateRequest):
    """Regenerate a specific content chunk using AI with type-aware prompts."""
    from openai import OpenAI
    from .config_fastapi import settings

    if not settings.LLM_API_KEY:
        raise HTTPException(status_code=500, detail="LLM_API_KEY not configured")

    # Build system prompt with topic context
    system_prompt = "You are an expert educational content enhancer specializing in clear, engaging learning materials."
    if request.subtopic_name:
        system_prompt += f" The content belongs to the subtopic: '{request.subtopic_name}'."
    if request.focus:
        system_prompt += f" Enhancement focus: {request.focus}."

    # Get type-specific instructions
    type_instruction = CHUNK_TYPE_PROMPTS.get(request.type, CHUNK_TYPE_PROMPTS["text"])

    # Build context from surrounding chunks
    context_section = ""
    if request.surrounding_context:
        before = request.surrounding_context.get("before", "").strip()
        after = request.surrounding_context.get("after", "").strip()
        if before or after:
            context_section = "\n\nSurrounding content for context (do NOT include this in your output):"
            if before:
                context_section += f"\n[BEFORE]: {before[:500]}"
            if after:
                context_section += f"\n[AFTER]: {after[:500]}"

    # Temperature-based tone guidance
    temp = request.temperature or 0.7
    tone = ""
    if temp > 0.7:
        tone = "Be more creative, use vivid language and metaphors where appropriate."
    elif temp < 0.5:
        tone = "Keep it clear, concise, and straightforward."

    user_prompt = f"""{type_instruction}

{tone}

Original Content:
{request.content}
{context_section}

IMPORTANT: Return ONLY the enhanced HTML content. No markdown code fences, no commentary, no explanations. Just the raw HTML."""

    try:
        client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_API_URL
        )

        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=temp,
            timeout=60,
        )

        enhanced_content = response.choices[0].message.content
        if enhanced_content:
            # Thorough cleanup
            enhanced_content = enhanced_content.strip()
            enhanced_content = re.sub(r'^```(?:html)?\n|```$', '', enhanced_content, flags=re.MULTILINE).strip()
            enhanced_content = re.sub(r'<style[^>]*>.*?</style>', '', enhanced_content, flags=re.DOTALL | re.IGNORECASE)
            enhanced_content = re.sub(r'<html[^>]*>|</html>|<head[^>]*>.*?</head>|<body[^>]*>|</body>|<!DOCTYPE[^>]*>', '', enhanced_content, flags=re.DOTALL | re.IGNORECASE).strip()
            return {"success": True, "content": enhanced_content}
        else:
            raise HTTPException(status_code=502, detail="LLM returned empty content")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chunk regeneration failed: {str(e)}")


class ContentImageRequest(BaseModel):
    """Request model for generating a content image."""
    prompt: str


def _generate_single_image_v8(prompt: str) -> Dict[str, Any]:
    """Internal helper to generate an image and return URL/filename."""
    import requests as http_requests
    from io import BytesIO
    from PIL import Image as PILImage
    from .config_fastapi import settings

    if not settings.LLM_API_KEY:
        raise Exception("LLM_API_KEY not configured")

    api_url = settings.LLM_API_URL.rstrip('/') if settings.LLM_API_URL else ''
    if not api_url:
        raise Exception("LLM_API_URL not configured")
    if not api_url.endswith('/chat/completions'):
        api_url = f"{api_url}/chat/completions" if api_url.endswith('/v1') else f"{api_url}/v1/chat/completions"

    full_prompt = f"Generate an image: {prompt}"

    response = http_requests.post(
        api_url,
        headers={
            "Authorization": f"Bearer {settings.LLM_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "grok-imagine-1.0",
            "messages": [{"role": "user", "content": full_prompt}]
        },
        timeout=120
    )

    if response.status_code != 200:
        raise Exception(f"Image API returned status {response.status_code}: {response.text[:200]}")

    result = response.json()
    content = result.get('choices', [{}])[0].get('message', {}).get('content', '')

    match = re.search(r'!\[.*?\]\((https://[^)]+)\)', content)
    if not match:
        raise Exception("Image generation did not return an image URL")

    image_url = match.group(1)
    served_url = image_url
    filename = None

    try:
        img_response = None
        download_headers = {"User-Agent": "Mozilla/5.0 (compatible; Sugarclass/1.0)"}
        for attempt in range(2):
            try:
                img_response = http_requests.get(image_url, timeout=15, headers=download_headers)
                if img_response.status_code == 200:
                    break
            except Exception:
                pass
            time.sleep(2)

        if img_response and img_response.status_code == 200:
            gen_images_dir = APP_DIR / "generated_images"
            gen_images_dir.mkdir(parents=True, exist_ok=True)

            filename = f"content_{uuid.uuid4().hex[:12]}.jpg"
            img_path = gen_images_dir / filename

            img = PILImage.open(BytesIO(img_response.content))
            if img.mode in ('RGBA', 'LA'):
                background = PILImage.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            img.save(img_path, 'JPEG', quality=90)
            served_url = f"/generated_images/{filename}"
    except Exception:
        pass  # Fallback to remote URL

    return {
        "success": True,
        "image_url": served_url,
        "filename": filename or image_url.split("/")[-1],
        "prompt": prompt
    }


@router.post("/generate-content-image", response_model=Dict[str, Any])
async def generate_content_image(request: ContentImageRequest):
    """Generate an image using grok-image-1.0 and return its URL."""
    try:
        res = _generate_single_image_v8(request.prompt)
        return res
    except Exception as e:
        if "not configured" in str(e):
            raise HTTPException(status_code=500, detail=str(e))
        raise HTTPException(status_code=502, detail=str(e))


# ============================================================================
# BACKGROUND TASK FUNCTIONS
# ============================================================================

def run_v8_generation_task(task_id: str, subtopic_id: str, options: Dict):
    """Background task to generate V8 content"""
    # Register a cancel event for this task so cancel_task() can wake us instantly
    _cancel_event = threading.Event()
    _cancel_events[task_id] = _cancel_event

    def update_task(status: str, progress: int, message: str, error: str = None):
        conn = None
        try:
            conn = get_db_connection()
            conn.execute("""
                UPDATE v8_processing_tasks
                SET status = ?, progress = ?, message = ?, error = ?, started_at = COALESCE(started_at, CURRENT_TIMESTAMP)
                WHERE task_id = ?
            """, (status, progress, message, error, task_id))
            conn.commit()

            if status in ['completed', 'failed', 'cancelled']:
                conn.execute("""
                    UPDATE v8_processing_tasks
                    SET completed_at = COALESCE(completed_at, CURRENT_TIMESTAMP)
                    WHERE task_id = ?
                """, (task_id,))
                if status == 'cancelled':
                    try:
                        conn.execute("""
                            UPDATE v8_processing_tasks
                            SET cancelled_at = COALESCE(cancelled_at, CURRENT_TIMESTAMP)
                            WHERE task_id = ?
                        """, (task_id,))
                    except Exception:
                        # Older schemas may not have cancelled_at yet.
                        pass
                conn.commit()
        except Exception as e:
            print(f"[V8][{task_id}] update_task failed: {e}")
        finally:
            if conn:
                conn.close()

    def add_log(level: str, message: str):
        conn = None
        try:
            conn = get_db_connection()
            conn.execute("""
                INSERT INTO v8_task_logs (task_id, log_level, message)
                VALUES (?, ?, ?)
            """, (task_id, level, message))
            conn.commit()
        except Exception as e:
            print(f"[V8][{task_id}] add_log failed ({level}): {e} | {message}")
        finally:
            if conn:
                conn.close()

    class TaskCancelledError(Exception):
        pass

    def is_cancel_requested() -> bool:
        # Fast path: check the in-memory event first (set by cancel_task() immediately)
        if _cancel_event.is_set():
            return True
        # Fallback: check DB (catches cases where the event wasn't registered, e.g. after restart)
        conn = None
        try:
            conn = get_db_connection()
            try:
                row = conn.execute("""
                    SELECT status, cancel_requested
                    FROM v8_processing_tasks
                    WHERE task_id = ?
                """, (task_id,)).fetchone()
            except Exception:
                row = conn.execute("""
                    SELECT status
                    FROM v8_processing_tasks
                    WHERE task_id = ?
                """, (task_id,)).fetchone()

            if not row:
                return False

            status = (row['status'] or '').lower()
            cancel_requested = False
            if 'cancel_requested' in row.keys():
                cancel_requested = bool(row['cancel_requested'])

            return cancel_requested or status in ('cancelling', 'cancelled')
        except Exception as e:
            print(f"[V8][{task_id}] is_cancel_requested failed: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def abort_if_cancelled(progress: Optional[int] = None, phase: str = ""):
        if not is_cancel_requested():
            return
        phase_suffix = f" during {phase}" if phase else ""
        add_log('warning', f"Cancellation requested{phase_suffix}. Stopping task.")
        update_task('cancelled', progress if progress is not None else 0, 'Task cancelled by user')
        raise TaskCancelledError("Task cancelled by user")

    processor = None
    hierarchy_conn = None
    try:
        # Import here to avoid circular imports
        from .processors.content_processor_v8 import V8Processor, GeminiClient

        abort_if_cancelled(0, 'startup')
        add_log('info', f"Starting V8 generation for subtopic {subtopic_id}")
        update_task('running', 10, 'Initializing...')
        abort_if_cancelled(10, 'initialization')

        # Load subtopic data
        conn = get_db_connection()
        hierarchy_conn = conn
        try:
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
        finally:
            conn.close()

        add_log('info', f"Loaded markdown: {len(markdown_content)} chars")
        update_task('running', 20, 'Analyzing structure...')
        abort_if_cancelled(20, 'structure analysis')

        generate_svgs = options.get('generate_svgs', True)
        generate_quiz = options.get('generate_quiz', True)
        generate_flashcards = options.get('generate_flashcards', True)
        if options.get('generate_images', False):
            add_log('warning', "generate_images=true requested, but image generation is not implemented in this task yet.")

        # Initialize generator
        processor = V8Processor()

        # Check if API is configured
        if not processor.gemini:
            raise Exception("LLM API key not configured. Set LLM_API_KEY or GEMINI_API_KEY environment variable.")

        # Analyze structure
        abort_if_cancelled(20, 'structure analysis')
        concepts = processor.gemini.analyze_structure(markdown_content)

        if not concepts:
            concepts = processor.generator._get_fallback_concepts(subtopic['name'])

        add_log('info', f"Identified {len(concepts)} concepts")
        update_task('running', 30, f'Found {len(concepts)} concepts')

        # Save concepts (clear existing first)
        conn = get_db_connection()
        conn.execute(
            "DELETE FROM v8_generated_content WHERE concept_id IN (SELECT id FROM v8_concepts WHERE subtopic_id = ?)",
            (subtopic_id,)
        )
        conn.execute("DELETE FROM v8_concepts WHERE subtopic_id = ?", (subtopic_id,))
        conn.commit()
        conn.close()
        hierarchy_conn = None

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
        concept_total = max(1, len(saved_concepts))

        # Generate SVGs and bullets
        for i, concept in enumerate(saved_concepts):
            concept_progress_start = 40 + int(40 * i / concept_total)
            abort_if_cancelled(concept_progress_start, f"concept {i+1}/{len(saved_concepts)}")

            if generate_svgs:
                add_log('info', f"Generating SVG for: {concept['title']}")
                svg = processor.gemini.generate_svg(concept['title'], concept['description'])
                if svg:
                    processor.db.update_generated_content(concept['id'], 'svg', svg)
                    if 'fallback-svg' in svg:
                        add_log('warning', f"⚠ SVG fallback used for {concept['title']}")
                    else:
                        add_log('info', f"✓ SVG generated for {concept['title']}")
            else:
                add_log('info', f"Skipping SVG generation for: {concept['title']}")

            abort_if_cancelled(concept_progress_start, f"bullets for concept {i+1}/{len(saved_concepts)}")
            bullets = processor.gemini.generate_bullets(
                concept['title'],
                concept['description'],
                markdown_content
            )
            if bullets:
                processor.db.update_generated_content(concept['id'], 'bullets', bullets)
                add_log('info', f"✓ Bullets generated for {concept['title']}")

            progress = 40 + int(40 * (i + 1) / concept_total)
            update_task('running', progress, f'Processing concept {i+1}/{len(saved_concepts)}')

        # Generate quiz
        if generate_quiz:
            add_log('info', "Generating quiz...")
            update_task('running', 85, 'Generating quiz...')
            abort_if_cancelled(85, 'quiz generation')

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
        if generate_flashcards:
            add_log('info', "Generating flashcards...")
            update_task('running', 90, 'Generating flashcards...')
            abort_if_cancelled(90, 'flashcard generation')

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
        abort_if_cancelled(95, 'finalization')
        processor.db.mark_subtopic_processed(subtopic_id)

        add_log('info', "V8 generation complete!")
        update_task('completed', 100, 'V8 content generation complete!')

    except TaskCancelledError:
        # Cancellation already recorded via abort_if_cancelled.
        pass
    except Exception as e:
        import traceback
        error_msg = str(e)
        add_log('error', error_msg)
        add_log('error', traceback.format_exc())
        update_task('failed', 0, 'Generation failed', error_msg)
    finally:
        if processor:
            processor.close()
        if hierarchy_conn:
            try:
                hierarchy_conn.close()
            except Exception:
                pass


def run_svg_regeneration(task_id: str, concept_id: int, concept: Dict, custom_prompt: Optional[str] = None):
    """Background task to regenerate SVG"""

    def update_task(status: str, message: str):
        conn = None
        try:
            conn = get_db_connection()
            conn.execute("""
                UPDATE v8_processing_tasks
                SET status = ?, message = ?, started_at = COALESCE(started_at, CURRENT_TIMESTAMP)
                WHERE task_id = ?
            """, (status, message, task_id))
            conn.commit()
        except Exception as e:
            print(f"[V8][{task_id}] svg update_task failed: {e}")
        finally:
            if conn:
                conn.close()

    processor = None
    try:
        from .processors.content_processor_v8 import V8Processor

        update_task('running', 'Regenerating SVG...')

        processor = V8Processor()
        if not processor.gemini:
            raise Exception("LLM API key not configured")
        
        # Use custom prompt if provided, otherwise default to concept description
        prompt_to_use = custom_prompt if custom_prompt else concept['description']
        svg = processor.gemini.generate_svg(concept['title'], prompt_to_use)

        if svg:
            processor.db.update_generated_content(concept_id, 'svg', svg)
            if 'fallback-svg' in svg:
                update_task('completed', 'SVG regenerated with fallback diagram')
            else:
                update_task('completed', 'SVG regenerated successfully')
        else:
            update_task('failed', 'Failed to regenerate SVG')

    except Exception as e:
        update_task('failed', f'Error: {str(e)}')
    finally:
        if processor:
            processor.close()


# ============================================================================
# FULL V8 INGESTION (Upload → Split → Generate)
# ============================================================================

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"


def _sanitize_code(name: str) -> str:
    """Generate a safe code from a name (e.g. 'Physics 0625' -> 'physics_0625')"""
    code = re.sub(r'[^\w\s-]', '', name).strip().lower()
    code = re.sub(r'[-\s]+', '_', code)
    return code


def _resolve_upload_markdown_path(batch_id: str, filename: str) -> Path:
    """Resolve and validate upload markdown path to prevent traversal."""
    safe_batch_id = (batch_id or "").strip()
    safe_filename = (filename or "").strip()

    if not safe_batch_id or not safe_filename:
        raise HTTPException(status_code=400, detail="batch_id and filename are required")

    # Only allow simple single-segment names
    if Path(safe_batch_id).name != safe_batch_id or Path(safe_filename).name != safe_filename:
        raise HTTPException(status_code=400, detail="Invalid batch_id or filename")

    if not safe_filename.lower().endswith(".md"):
        raise HTTPException(status_code=400, detail="Only markdown (.md) files are allowed for V8 ingestion")

    upload_root = UPLOAD_DIR.resolve()
    batch_dir = (UPLOAD_DIR / safe_batch_id).resolve()
    file_path = (batch_dir / safe_filename).resolve()

    if upload_root not in file_path.parents or file_path.parent != batch_dir:
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {safe_filename}")

    return file_path


def ensure_v8_tables():
    """Defensive check to ensure V8 tables exist before performing operations."""
    try:
        from .main import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='v8_processing_tasks'")
        exists = cursor.fetchone()
        conn.close()
        
        if not exists:
            import logging
            logger = logging.getLogger("uvicorn")
            logger.info("[V8 Admin] v8_processing_tasks table not found, running migration...")
            from .init_v8_db import migrate_to_v8
            migrate_to_v8()
    except Exception as e:
        import logging
        logger = logging.getLogger("uvicorn")
        logger.error(f"[V8 Admin] Error ensuring V8 tables: {e}")


def ensure_v8_task_columns():
    """Ensure task control columns exist on v8_processing_tasks."""
    conn = None
    try:
        conn = get_db_connection()
        cols = conn.execute("PRAGMA table_info(v8_processing_tasks)").fetchall()
        col_names = {row["name"] for row in cols}
        if "cancel_requested" not in col_names:
            conn.execute("ALTER TABLE v8_processing_tasks ADD COLUMN cancel_requested INTEGER DEFAULT 0")
        if "cancelled_at" not in col_names:
            conn.execute("ALTER TABLE v8_processing_tasks ADD COLUMN cancelled_at TIMESTAMP")
        conn.commit()
    except Exception as e:
        print(f"[V8] ensure_v8_task_columns failed: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

@router.post("/ingest")
async def v8_ingest(request: V8IngestRequest, background_tasks: BackgroundTasks):
    """Full V8 ingestion: markdown → split → create hierarchy → generate V8 content for ALL subtopics"""
    
    # Defensive check for tables
    ensure_v8_tables()
    ensure_v8_task_columns()

    subject_name = (request.subject_name or "").strip()
    syllabus = (request.syllabus or "").strip() or "IGCSE"
    if not subject_name:
        raise HTTPException(status_code=400, detail="subject_name is required")

    file_path = _resolve_upload_markdown_path(request.batch_id, request.filename)

    task_id = str(uuid.uuid4())

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO v8_processing_tasks (task_id, task_type, status, progress, message)
        VALUES (?, 'full_ingestion', 'pending', 0, 'Task created')
    """, (task_id,))
    conn.commit()
    conn.close()

    background_tasks.add_task(
        run_v8_full_ingestion,
        task_id=task_id,
        file_path=file_path,
        subject_name=subject_name,
        syllabus=request.syllabus,
        target_subject_id=request.target_subject_id,
        exam_board=request.exam_board,
        ib_level=request.ib_level,
    )

    return {"task_id": task_id, "status": "pending", "message": "V8 full ingestion started"}


def run_v8_full_ingestion(
    task_id: str,
    file_path: str,
    subject_name: str,
    syllabus: str,
    target_subject_id: Optional[str] = None,
    exam_board: Optional[str] = None,
    ib_level: Optional[str] = None
):
    """Background task: full V8 pipeline — parse markdown, create hierarchy, generate all V8 content"""
    # Register a cancel event for this task so cancel_task() can wake us instantly
    _cancel_event = threading.Event()
    _cancel_events[task_id] = _cancel_event

    def update_task(status: str, progress: int, message: str, error: str = None):
        conn = None
        try:
            conn = get_db_connection()
            conn.execute("""
                UPDATE v8_processing_tasks
                SET status = ?, progress = ?, message = ?, error = ?, started_at = COALESCE(started_at, CURRENT_TIMESTAMP)
                WHERE task_id = ?
            """, (status, progress, message, error, task_id))
            conn.commit()
            if status in ['completed', 'failed', 'cancelled']:
                conn.execute("""
                    UPDATE v8_processing_tasks
                    SET completed_at = COALESCE(completed_at, CURRENT_TIMESTAMP)
                    WHERE task_id = ?
                """, (task_id,))
                if status == 'cancelled':
                    try:
                        conn.execute("""
                            UPDATE v8_processing_tasks
                            SET cancelled_at = COALESCE(cancelled_at, CURRENT_TIMESTAMP)
                            WHERE task_id = ?
                        """, (task_id,))
                    except Exception:
                        # Older schemas may not have cancelled_at yet.
                        pass
                conn.commit()
        except Exception as e:
            print(f"[V8][{task_id}] update_task failed: {e}")
        finally:
            if conn:
                conn.close()

    def add_log(level: str, message: str):
        conn = None
        try:
            conn = get_db_connection()
            conn.execute("""
                INSERT INTO v8_task_logs (task_id, log_level, message)
                VALUES (?, ?, ?)
            """, (task_id, level, message))
            conn.commit()
        except Exception as e:
            print(f"[V8][{task_id}] add_log failed ({level}): {e} | {message}")
        finally:
            if conn:
                conn.close()

    class TaskCancelledError(Exception):
        pass

    def is_cancel_requested() -> bool:
        # Fast path: check the in-memory event first (set by cancel_task() immediately)
        if _cancel_event.is_set():
            return True
        # Fallback: check DB
        conn = None
        try:
            conn = get_db_connection()
            try:
                row = conn.execute("SELECT status, cancel_requested FROM v8_processing_tasks WHERE task_id = ?", (task_id,)).fetchone()
            except Exception:
                row = conn.execute("SELECT status FROM v8_processing_tasks WHERE task_id = ?", (task_id,)).fetchone()

            if not row:
                return False

            status = (row['status'] or '').lower()
            cancel_requested = False
            if 'cancel_requested' in row.keys():
                cancel_requested = bool(row['cancel_requested'])

            return cancel_requested or status in ('cancelling', 'cancelled')
        except Exception as e:
            print(f"[V8][{task_id}] is_cancel_requested failed: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def abort_if_cancelled(progress: Optional[int] = None, phase: str = ""):
        if not is_cancel_requested():
            return
        phase_suffix = f" during {phase}" if phase else ""
        add_log('warning', f"Cancellation requested{phase_suffix}. Stopping task.")
        update_task('cancelled', progress if progress is not None else 0, 'Task cancelled by user')
        raise TaskCancelledError("Task cancelled by user")

    processor = None
    hierarchy_conn = None
    try:
        from .processors.content_processor_v8 import ContentSplitter, V8Processor, GeminiClient, ConceptData

        abort_if_cancelled(0, 'startup')
        add_log('info', f"Starting V8 full ingestion for: {subject_name}")
        update_task('running', 5, 'Reading markdown file...')
        abort_if_cancelled(5, 'startup')

        # --- Step 1: Read markdown ---
        md_path = Path(file_path)
        with open(md_path, 'r', encoding='utf-8', errors='ignore') as f:
            markdown_content = f.read()

        add_log('info', f"Read {len(markdown_content)} chars from {md_path.name}")
        update_task('running', 10, 'Splitting content into chapters and subtopics...')
        abort_if_cancelled(10, 'content split')

        # --- Step 2: Split into chapters and subtopics ---
        splitter = ContentSplitter(markdown_content)
        subtopic_list = splitter.split()

        # Also extract chapters from splitter for topic creation
        # Re-parse to get chapter→subtopic mapping
        chapters = _extract_chapters_with_subtopics(markdown_content, subtopic_list)

        if not chapters:
            # Fallback: put everything under a single "General" topic
            chapters = [{'num': '1', 'title': subject_name, 'subtopics': subtopic_list}]

        total_subtopics = sum(len(ch['subtopics']) for ch in chapters)
        add_log('info', f"Found {len(chapters)} chapters, {total_subtopics} subtopics")

        if total_subtopics == 0:
            raise Exception("No subtopics detected in the markdown file. Check the heading format.")

        update_task('running', 15, f'Creating hierarchy: {len(chapters)} topics, {total_subtopics} subtopics...')
        abort_if_cancelled(15, 'hierarchy creation')

        # --- Step 3: Create/find syllabus and subject ---
        conn = get_db_connection()
        hierarchy_conn = conn

        # Detect schema type: old schema uses TEXT PRIMARY KEY, V8 uses INTEGER AUTOINCREMENT
        col_info = conn.execute("PRAGMA table_info(syllabuses)").fetchall()
        col_names = [c['name'] for c in col_info]
        id_type = next((c['type'] for c in col_info if c['name'] == 'id'), 'TEXT')
        is_v8_schema = id_type.upper() == 'INTEGER' and 'display_name' in col_names

        add_log('info', f"Schema type: {'V8' if is_v8_schema else 'legacy'} (id type: {id_type})")

        # Append HL/SL to subject name if provided (IB subjects)
        display_subject_name = subject_name
        if ib_level:
            display_subject_name = f"{subject_name} {ib_level}"
            add_log('info', f"Processing IB subject: {display_subject_name}")

        syllabus_code = _sanitize_code(syllabus)
        subject_code = _sanitize_code(display_subject_name) # Use display_subject_name for code
        requested_subject_id = (target_subject_id or "").strip().lower()
        requested_subject_id = re.sub(r'[^a-z0-9_]', '', requested_subject_id)
        if requested_subject_id:
            if requested_subject_id.startswith(f"{syllabus_code}_"):
                subject_text_id = requested_subject_id
            else:
                subject_text_id = f"{syllabus_code}_{requested_subject_id}"
        else:
            subject_text_id = f"{syllabus_code}_{subject_code}"

        if is_v8_schema:
            # V8 schema: INTEGER AUTOINCREMENT ids
            conn.execute("INSERT OR IGNORE INTO syllabuses (name, display_name) VALUES (?, ?)", (syllabus, syllabus))
            conn.commit()
            syllabus_row = conn.execute("SELECT id FROM syllabuses WHERE name = ?", (syllabus,)).fetchone()
            syllabus_id = syllabus_row['id']

            conn.execute("""
                INSERT OR IGNORE INTO subjects (syllabus_id, subject_id, name, code)
                VALUES (?, ?, ?, ?)
            """, (syllabus_id, subject_text_id, display_subject_name, exam_board or subject_code)) # Use display_subject_name
            conn.commit()
            subject_row = conn.execute("SELECT id FROM subjects WHERE subject_id = ?", (subject_text_id,)).fetchone()
        else:
            # Legacy schema: TEXT PRIMARY KEY ids
            conn.execute("INSERT OR IGNORE INTO syllabuses (id, name) VALUES (?, ?)", (syllabus_code, syllabus))
            conn.commit()
            syllabus_row = conn.execute("SELECT id FROM syllabuses WHERE id = ?", (syllabus_code,)).fetchone()
            syllabus_id = syllabus_row['id']

            conn.execute("""
                INSERT OR IGNORE INTO subjects (id, syllabus_id, name)
                VALUES (?, ?, ?)
            """, (subject_text_id, syllabus_id, display_subject_name)) # Use display_subject_name
            conn.commit()
            subject_row = conn.execute("SELECT id FROM subjects WHERE id = ?", (subject_text_id,)).fetchone()

        subject_db_id = subject_row['id']

        add_log('info', f"Subject: {display_subject_name} (id={subject_db_id}, code={subject_text_id})")

        # --- Step 4: Create topics and subtopics ---
        subtopic_db_ids = []  # (db_id, markdown_content) pairs for V8 generation

        for ch_idx, chapter in enumerate(chapters):
            abort_if_cancelled(15, f"topic creation {ch_idx + 1}/{len(chapters)}")
            topic_code = f"T{ch_idx + 1}"
            topic_name = chapter['title']

            # Insert topic - try V8 schema first, fallback to old schema
            try:
                conn.execute("""
                    INSERT INTO topics (subject_id, topic_id, name, order_num)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(subject_id, topic_id) DO UPDATE SET
                        name = excluded.name,
                        order_num = excluded.order_num
                """, (subject_db_id, topic_code, topic_name, ch_idx + 1))
                conn.commit()
                topic_row = conn.execute(
                    "SELECT id FROM topics WHERE subject_id = ? AND topic_id = ?",
                    (subject_db_id, topic_code)
                ).fetchone()
            except Exception:
                # Fallback: old schema uses TEXT id as primary key
                text_topic_id = f"{subject_text_id}_{topic_code}"
                conn.execute("""
                    INSERT OR REPLACE INTO topics (id, subject_id, name, order_num)
                    VALUES (?, ?, ?, ?)
                """, (text_topic_id, subject_db_id, topic_name, ch_idx + 1))
                conn.commit()
                topic_row = conn.execute(
                    "SELECT id FROM topics WHERE id = ?",
                    (text_topic_id,)
                ).fetchone()

            topic_db_id = topic_row['id']

            for st_idx, subtopic in enumerate(chapter['subtopics']):
                abort_if_cancelled(15, f"subtopic mapping {ch_idx + 1}.{st_idx + 1}")
                subtopic_text_id = (subtopic.get('num') or f"{ch_idx+1}.{st_idx+1}").strip()
                subtopic_slug = subtopic.get('slug') or _sanitize_code(subtopic['title'])
                subtopic_name = subtopic['title']
                subtopic_content = subtopic.get('content', '')

                # Insert subtopic - try V8 schema first, fallback to old schema
                try:
                    conn.execute("""
                        INSERT INTO subtopics (topic_id, subtopic_id, slug, name, order_num, markdown_file_path)
                        VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(topic_id, subtopic_id) DO UPDATE SET
                            slug = excluded.slug,
                            name = excluded.name,
                            order_num = excluded.order_num,
                            markdown_file_path = excluded.markdown_file_path
                    """, (topic_db_id, subtopic_text_id, subtopic_slug, subtopic_name, st_idx + 1, str(md_path)))
                    conn.commit()
                    st_row = conn.execute(
                        "SELECT id FROM subtopics WHERE topic_id = ? AND subtopic_id = ?",
                        (topic_db_id, subtopic_text_id)
                    ).fetchone()
                except Exception:
                    # Fallback: old schema uses TEXT id, simpler columns
                    text_subtopic_id = f"{subject_text_id}_{subtopic_text_id}"
                    conn.execute("""
                        INSERT OR REPLACE INTO subtopics (id, topic_id, name, order_num)
                        VALUES (?, ?, ?, ?)
                    """, (text_subtopic_id, topic_db_id, subtopic_name, st_idx + 1))
                    conn.commit()
                    st_row = conn.execute(
                        "SELECT id FROM subtopics WHERE id = ?",
                        (text_subtopic_id,)
                    ).fetchone()

                st_db_id = st_row['id']

                # Store markdown content in content_raw for later use.
                # Use an explicit check-then-INSERT-or-UPDATE so we never create
                # duplicate rows on re-ingestion.  (The legacy content_raw table often
                # has no UNIQUE constraint on subtopic_id, so ON CONFLICT upserts don't work everywhere.)
                content_saved = False
                try:
                    existing_raw = conn.execute(
                        "SELECT id FROM content_raw WHERE subtopic_id = ? ORDER BY id LIMIT 1",
                        (st_db_id,)
                    ).fetchone()
                    if existing_raw:
                        conn.execute("""
                            UPDATE content_raw
                            SET title = ?, markdown_content = ?, source_file = ?, char_count = ?
                            WHERE id = ?
                        """, (subtopic_name, subtopic_content, str(md_path), len(subtopic_content), existing_raw['id']))
                    else:
                        conn.execute("""
                            INSERT INTO content_raw (subtopic_id, title, markdown_content, source_file, char_count)
                            VALUES (?, ?, ?, ?, ?)
                        """, (st_db_id, subtopic_name, subtopic_content, str(md_path), len(subtopic_content)))
                    conn.commit()
                    content_saved = True
                except Exception as e1:
                    add_log('warning', f"  Could not save content_raw for {subtopic_name}: {e1}")
                    # Fallback to simple update if needed
                    try:
                        existing_raw = conn.execute(
                            "SELECT id FROM content_raw WHERE subtopic_id = ? LIMIT 1",
                            (st_db_id,)
                        ).fetchone()
                        if existing_raw:
                            conn.execute(
                                "UPDATE content_raw SET markdown_content = ? WHERE id = ?",
                                (subtopic_content, existing_raw['id'])
                            )
                        else:
                            conn.execute(
                                "INSERT INTO content_raw (subtopic_id, markdown_content) VALUES (?, ?)",
                                (st_db_id, subtopic_content)
                            )
                        conn.commit()
                        content_saved = True
                    except Exception as e2:
                        add_log('warning', f"  Critical error saving content_raw for {subtopic_name}: {e2}")

                if content_saved:
                    add_log('info', f"  Saved content_raw for {subtopic_name} ({len(subtopic_content)} chars)")
                else:
                    add_log('warning', f"  content_raw not saved for {subtopic_name} - V8 generation will use inline content")

                subtopic_db_ids.append((st_db_id, subtopic_name, subtopic_content))

        conn.close()
        hierarchy_conn = None

        add_log('info', f"Created {len(chapters)} topics, {len(subtopic_db_ids)} subtopics in database")
        update_task('running', 20, f'Starting V8 generation for {len(subtopic_db_ids)} subtopics...')
        abort_if_cancelled(20, 'generation bootstrap')

        # --- Step 5: Generate V8 content for each subtopic ---
        processor = V8Processor()

        if not processor.gemini:
            add_log('error', 'LLM API key not configured. Set LLM_API_KEY or GEMINI_API_KEY.')
            raise Exception("LLM API key not configured. Set LLM_API_KEY or GEMINI_API_KEY environment variable.")

        # Log API configuration for debugging
        from .processors.content_processor_v8 import API_BASE_URL, API_KEY, MODEL
        from .processors.content_processor_v8 import SubtopicCache, GrokImageClient, ENABLE_CACHE, ENABLE_REWRITE, ENABLE_IMAGES, GROK_API_KEY
        add_log('info', f"LLM Config: model={MODEL}, url={API_BASE_URL[:60]}..., key={'set (' + API_KEY[:8] + '...)' if API_KEY else 'NOT SET'}")
        add_log('info', f"Features: cache={ENABLE_CACHE}, rewrite={ENABLE_REWRITE}, images={ENABLE_IMAGES}")

        # Initialize Grok client if images are enabled
        grok_client = GrokImageClient() if (ENABLE_IMAGES and GROK_API_KEY) else None
        if ENABLE_IMAGES and not grok_client:
            add_log('warning', 'Image generation disabled: GROK_API_KEY not set')

        total_success = 0
        total_failed = 0
        completed_count = 0
        progress_lock = threading.Lock()

        from .processors.content_processor_v8 import PARALLEL_WORKERS
        num_workers = max(1, min(PARALLEL_WORKERS, len(subtopic_db_ids)))
        add_log('info', f"Parallel workers: {num_workers} (V8_PARALLEL_WORKERS={PARALLEL_WORKERS})")

        # --- Thread-local V8Processor pool ---
        _thread_local = threading.local()

        def _get_thread_processor():
            """Get or create a V8Processor for the current thread."""
            if not hasattr(_thread_local, 'processor'):
                _thread_local.processor = V8Processor()
            return _thread_local.processor

        def _process_single_subtopic(args):
            """Process a single subtopic — runs in a worker thread."""
            nonlocal total_success, total_failed, completed_count
            i, (st_db_id, st_name, st_content) = args
            n = len(subtopic_db_ids)

            try:
                # Check for cancellation at start
                if _cancel_event.is_set() or is_cancel_requested():
                    return

                proc = _get_thread_processor()
                add_log('info', f"[{i+1}/{n}] Processing: {st_name}")

                # --- Progress calculation ---
                subtopic_progress_base = 20 + int(75 * i / n)
                subtopic_progress_end = 20 + int(75 * (i + 1) / n)
                subtopic_progress_span = max(1, subtopic_progress_end - subtopic_progress_base)

                concepts_phase_start = min(
                    subtopic_progress_end,
                    subtopic_progress_base + max(1, int(subtopic_progress_span * 0.15))
                )
                concepts_phase_end = min(
                    subtopic_progress_end,
                    max(concepts_phase_start, subtopic_progress_base + max(2, int(subtopic_progress_span * 0.75)))
                )
                quiz_phase_progress = min(
                    subtopic_progress_end,
                    max(concepts_phase_end, subtopic_progress_base + max(2, int(subtopic_progress_span * 0.85)))
                )
                flashcards_phase_progress = min(
                    subtopic_progress_end,
                    max(quiz_phase_progress, subtopic_progress_base + max(3, int(subtopic_progress_span * 0.92)))
                )

                # --- Cache check ---
                st_hash = hashlib.md5(st_content.encode('utf-8', errors='ignore')).hexdigest()
                if ENABLE_CACHE:
                    cache = SubtopicCache(st_db_id, st_hash)
                    cached = cache.load()
                    if cached:
                        add_log('info', f"  [CACHE HIT] Skipping API calls for: {st_name}")
                        proc.db.mark_subtopic_processed(st_db_id)
                        with progress_lock:
                            total_success += 1
                            completed_count += 1
                            done = completed_count
                        update_task('running', subtopic_progress_end, f'[{done}/{n}] {st_name}: Done (cached)')
                        return
                else:
                    cache = None

                # --- Content for analysis ---
                if len(st_content) > 100:
                    content_for_analysis = st_content
                else:
                    content_for_analysis = f"# {st_name}\n\n" + markdown_content[:4000]
                add_log('info', f"  Content length: {len(content_for_analysis)} chars")

                # --- Analyze structure ---
                if _cancel_event.is_set():
                    return
                add_log('info', f"  Calling LLM: analyze_structure...")
                concepts = proc.gemini.analyze_structure(content_for_analysis)
                if not concepts:
                    add_log('warning', f"  LLM returned no concepts, using fallbacks")
                    concepts = proc.generator._get_fallback_concepts(st_name)
                else:
                    add_log('info', f"  LLM returned {len(concepts)} concepts")

                # Save concepts (clear existing first)
                conn = get_db_connection()
                try:
                    conn.execute("DELETE FROM v8_generated_content WHERE concept_id IN (SELECT id FROM v8_concepts WHERE subtopic_id = ?)", (st_db_id,))
                    conn.execute("DELETE FROM v8_concepts WHERE subtopic_id = ?", (st_db_id,))
                    conn.commit()
                except Exception as e:
                    add_log('warning', f"  Could not clear old V8 data (tables may not exist yet): {e}")
                conn.close()

                for ci, concept_data in enumerate(concepts):
                    concept = ConceptData(
                        concept_key=concept_data.get('id', f'concept_{ci}'),
                        title=concept_data.get('title', 'Concept'),
                        description=concept_data.get('description', ''),
                        icon=concept_data.get('icon', '📚'),
                        order_num=ci
                    )
                    proc.db.save_concepts(st_db_id, [concept])

                add_log('info', f"  Saved {len(concepts)} concepts to DB")

                # --- Generate SVGs and bullets for each concept ---
                saved_concepts = proc.db.get_concepts(st_db_id)
                concept_count = max(1, len(saved_concepts))
                for ci, concept in enumerate(saved_concepts):
                    if _cancel_event.is_set():
                        return
                    add_log('info', f"  Calling LLM: SVG for '{concept['title']}'...")
                    svg = proc.gemini.generate_svg(concept['title'], concept['description'])
                    if svg:
                        proc.db.update_generated_content(concept['id'], 'svg', svg)
                        if 'fallback-svg' in svg:
                            add_log('warning', f"    ⚠ SVG fallback used ({len(svg)} chars)")
                        else:
                            add_log('info', f"    ✓ SVG generated ({len(svg)} chars)")
                    else:
                        add_log('warning', f"    ✗ SVG generation returned empty")

                    add_log('info', f"  Calling LLM: bullets for '{concept['title']}'...")
                    bullets = proc.gemini.generate_bullets(concept['title'], concept['description'], content_for_analysis)
                    if bullets:
                        proc.db.update_generated_content(concept['id'], 'bullets', bullets)
                        add_log('info', f"    ✓ Bullets generated ({len(bullets)} chars)")
                    else:
                        add_log('warning', f"    ✗ Bullets generation returned empty")

                # --- Generate quiz ---
                if _cancel_event.is_set():
                    return
                conn = get_db_connection()
                try:
                    conn.execute("DELETE FROM v8_quiz_questions WHERE subtopic_id = ?", (st_db_id,))
                    conn.commit()
                except Exception:
                    pass
                conn.close()

                add_log('info', f"  Calling LLM: quiz generation...")
                quiz = proc.gemini.generate_quiz(st_name, content_for_analysis, 5)
                if quiz and quiz.get('questions'):
                    for qi, q in enumerate(quiz['questions'], 1):
                        proc.db.save_quiz_question(st_db_id, qi, q)
                    add_log('info', f"  ✓ Quiz: {len(quiz['questions'])} questions")
                else:
                    add_log('warning', f"  ✗ Quiz generation returned empty")

                # --- Generate flashcards ---
                if _cancel_event.is_set():
                    return
                conn = get_db_connection()
                try:
                    conn.execute("DELETE FROM v8_flashcards WHERE subtopic_id = ?", (st_db_id,))
                    conn.commit()
                except Exception:
                    pass
                conn.close()

                add_log('info', f"  Calling LLM: flashcard generation...")
                flashcards = proc.gemini.generate_flashcards(st_name, content_for_analysis, 8)
                if flashcards and flashcards.get('cards'):
                    for fi, card in enumerate(flashcards['cards'], 1):
                        proc.db.save_flashcard(st_db_id, fi, card.get('front', ''), card.get('back', ''))
                    add_log('info', f"  ✓ Flashcards: {len(flashcards['cards'])} cards")
                else:
                    add_log('warning', f"  ✗ Flashcard generation returned empty")

                # --- Rewrite content (if enabled) ---
                if ENABLE_REWRITE:
                    if _cancel_event.is_set():
                        return
                    add_log('info', f"  Calling LLM: rewrite_content...")
                    rewritten = proc.gemini.rewrite_content(content_for_analysis)
                    if rewritten:
                        proc.db.save_rewritten_content(st_db_id, rewritten)
                        add_log('info', f"  ✓ Rewritten content saved ({len(rewritten)} chars)")
                    else:
                        add_log('warning', f"  ✗ Content rewrite returned empty")

                # --- Real-life images (if enabled and Grok configured) ---
                if ENABLE_IMAGES and grok_client:
                    if _cancel_event.is_set():
                        return
                    add_log('info', f"  Calling LLM+Grok: generate_reallife_images...")
                    try:
                        images = proc.gemini.generate_reallife_images(st_name, content_for_analysis[:2000], grok_client)
                        for img in images:
                            if img.get('url'):
                                proc.db.save_reallife_image(
                                    st_db_id, img['id'], img['url'],
                                    img.get('prompt', ''), img.get('title', ''), img.get('description', '')
                                )
                        add_log('info', f"  ✓ Images: {len([img for img in images if img.get('url')])} generated")
                    except Exception as img_err:
                        add_log('warning', f"  ✗ Image generation failed: {img_err}")

                # --- Save to cache ---
                if cache is not None:
                    cache.save({'subtopic_name': st_name, 'completed': True})

                # Mark as processed
                proc.db.mark_subtopic_processed(st_db_id)
                add_log('info', f"  ✓ Completed: {st_name}")
                with progress_lock:
                    total_success += 1
                    completed_count += 1
                    done = completed_count
                update_task('running', subtopic_progress_end, f'[{done}/{n}] {st_name}: Done')

            except TaskCancelledError:
                raise
            except Exception as e:
                import traceback
                add_log('error', f"  ✗ Failed: {st_name}: {str(e)}")
                add_log('error', f"  Traceback: {traceback.format_exc()[-500:]}")
                with progress_lock:
                    total_failed += 1
                    completed_count += 1

        # --- Run subtopics in parallel ---
        from concurrent.futures import ThreadPoolExecutor, as_completed

        indexed_subtopics = list(enumerate(subtopic_db_ids))
        executor = ThreadPoolExecutor(max_workers=num_workers, thread_name_prefix="v8_worker")
        try:
            futures = {executor.submit(_process_single_subtopic, item): item for item in indexed_subtopics}
            for future in as_completed(futures):
                # Check cancellation
                if _cancel_event.is_set() or is_cancel_requested():
                    add_log('warning', 'Cancellation detected, shutting down workers...')
                    executor.shutdown(wait=False, cancel_futures=True)
                    abort_if_cancelled(completed_count * 100 // max(1, len(subtopic_db_ids)), 'parallel generation')
                    break
                # Propagate exceptions from workers
                try:
                    future.result()
                except TaskCancelledError:
                    add_log('warning', 'Worker cancelled, shutting down...')
                    executor.shutdown(wait=False, cancel_futures=True)
                    abort_if_cancelled(completed_count * 100 // max(1, len(subtopic_db_ids)), 'parallel generation')
                    break
                except Exception:
                    pass  # Already handled inside _process_single_subtopic
        finally:
            executor.shutdown(wait=True)
            # Close all thread-local processors
            # (Python threading.local doesn't expose all threads, but the GC will clean up)


        add_log('info', f"Generation summary: {total_success} succeeded, {total_failed} failed out of {len(subtopic_db_ids)}")
        if total_success == 0 and total_failed > 0:
            add_log('error', "V8 full ingestion failed for all subtopics")
            update_task('failed', 100, f'V8 ingestion failed: 0 succeeded, {total_failed} failed')
        elif total_failed > 0:
            add_log('warning', f"V8 full ingestion completed with warnings: {total_success} succeeded, {total_failed} failed")
            update_task('completed', 100, f'V8 ingestion partial: {total_success} succeeded, {total_failed} failed')
        else:
            add_log('info', f"V8 full ingestion complete! Processed {len(subtopic_db_ids)} subtopics.")
            update_task('completed', 100, f'V8 ingestion complete: {len(subtopic_db_ids)} subtopics processed')

    except TaskCancelledError:
        # Cancellation already recorded via abort_if_cancelled.
        pass
    except Exception as e:
        import traceback
        error_msg = str(e)
        add_log('error', error_msg)
        add_log('error', traceback.format_exc())
        update_task('failed', 0, 'Ingestion failed', error_msg)
    finally:
        if processor:
            processor.close()
        if hierarchy_conn:
            try:
                hierarchy_conn.close()
            except Exception:
                pass
        # Clean up the cancel event registry to avoid memory leaks
        _cancel_events.pop(task_id, None)


def _extract_chapters_with_subtopics(markdown_content: str, subtopic_list: list) -> list:
    """Map chapters → subtopics, preferring splitter-provided chapter metadata."""
    from .processors.content_processor_v8 import ContentSplitter

    chapters = []
    chapter_index = {}

    # Preferred path: ContentSplitter now annotates each subtopic with chapter metadata.
    has_chapter_metadata = any(
        (st.get('chapter_title') is not None) or (st.get('chapter_num') is not None)
        for st in subtopic_list
    )
    if has_chapter_metadata:
        for st in subtopic_list:
            chapter_title = (st.get('chapter_title') or '').strip() or 'General'
            chapter_num = str(st.get('chapter_num') or '').strip()
            key = f"{chapter_num}::{chapter_title}" if chapter_num else chapter_title
            if key not in chapter_index:
                chapter_index[key] = len(chapters)
                chapters.append({
                    'num': chapter_num or str(len(chapters) + 1),
                    'title': chapter_title,
                    'subtopics': []
                })
            chapters[chapter_index[key]]['subtopics'].append(st)

        if chapters:
            return chapters

    # Backward-compatible fallback for old splitter payloads without chapter metadata.
    lines = markdown_content.split('\n')
    temp_splitter = ContentSplitter("")
    current_chapter = None
    subtopic_idx = 0

    for line in lines:
        chapter_match = temp_splitter._match_chapter(line)
        if chapter_match:
            current_chapter = {
                'num': chapter_match['num'],
                'title': chapter_match['title'],
                'subtopics': []
            }
            chapters.append(current_chapter)
            continue

        subtopic_match = temp_splitter._match_subtopic(line)
        if subtopic_match and subtopic_idx < len(subtopic_list):
            st = subtopic_list[subtopic_idx]
            if current_chapter:
                current_chapter['subtopics'].append(st)
            else:
                if not chapters:
                    chapters.append({'num': '1', 'title': 'General', 'subtopics': []})
                chapters[-1]['subtopics'].append(st)
            subtopic_idx += 1

    while subtopic_idx < len(subtopic_list):
        if chapters:
            chapters[-1]['subtopics'].append(subtopic_list[subtopic_idx])
        else:
            chapters.append({'num': '1', 'title': 'General', 'subtopics': [subtopic_list[subtopic_idx]]})
        subtopic_idx += 1

    return chapters


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

    # Get real-life images
    reallife_images = conn.execute("""
        SELECT id, image_type, image_url, prompt, title, description
        FROM v8_reallife_images
        WHERE subtopic_id = ?
        ORDER BY image_type
    """, (subtopic_id,)).fetchall()

    conn.close()

    return {
        "subtopic_id": subtopic_id,
        "name": subtopic['name'],
        "concepts": concept_list,
        "quiz": [dict(q) for q in quiz],
        "flashcards": [dict(f) for f in flashcards],
        "reallife_images": [dict(img) for img in reallife_images]
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
