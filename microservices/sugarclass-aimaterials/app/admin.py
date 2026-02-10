"""
Exercise CRUD API endpoints
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
import sqlite3
import os
import uuid
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
import json

import re

from .exercise_builder import build_exercises_for_subtopic

router = APIRouter(prefix="/api/admin", tags=["admin"])

# Paths
BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SCRIPTS_DIR = BASE_DIR.parent / "scripts"

# Task tracking
tasks: Dict[str, Dict] = {}

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class IngestRequest(BaseModel):
    batch_id: str
    filename: str
    subject_name: str
    syllabus: str = "IB Diploma"

class ExerciseRequest(BaseModel):
    subtopic_id: str
    generate_images: bool = True
    count: int = 5

class ExerciseCreateRequest(BaseModel):
    subtopic_id: str
    question_text: str
    options: Dict[str, str]  # {"A": "option1", "B": "option2", ...}
    correct_answer: str
    explanation: Optional[str] = ""
    generate_image: bool = False
    image_prompt: Optional[str] = None

class ExerciseUpdateRequest(BaseModel):
    question_text: Optional[str] = None
    options: Optional[Dict[str, str]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    generate_image: bool = False
    image_prompt: Optional[str] = None


def extract_metadata_from_upload(batch_dir: Path, md_filename: str) -> Dict[str, Optional[str]]:
    """
    Extract subject name and syllabus from uploaded files.
    
    Priority for subject name:
    1. .structure.json file (if present)
    2. First H1 heading (# Title) in markdown
    3. Filename (fallback)
    
    Priority for syllabus:
    1. .structure.json file (if present)
    2. Default to "IB Diploma"
    """
    subject_name = None
    syllabus = "IB Diploma"
    
    # 1. Check for .structure.json first
    json_files = list(batch_dir.glob("*.structure.json"))
    if json_files:
        try:
            with open(json_files[0], 'r', encoding='utf-8') as f:
                structure = json.load(f)
                subject_name = structure.get("subject_name")
                syllabus = structure.get("syllabus", "IB Diploma")
                if subject_name:
                    return {"subject_name": subject_name, "syllabus": syllabus}
        except Exception as e:
            print(f"Warning: Could not read structure.json: {e}")
    
    # 2. Try to extract from markdown H1
    md_path = batch_dir / md_filename
    if md_path.exists():
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('# '):
                        subject_name = line[2:].strip()
                        break
        except Exception as e:
            print(f"Warning: Could not read markdown: {e}")
    
    # 3. Fallback to filename
    if not subject_name:
        subject_name = md_filename.replace('.md', '').replace('_', ' ').title()
    
    return {"subject_name": subject_name, "syllabus": syllabus}


# ============================================================================
# File Upload
# ============================================================================

@router.post("/upload", response_model=Dict[str, Any])
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload multiple files and return batch ID."""
    batch_id = str(uuid.uuid4())
    batch_dir = UPLOAD_DIR / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    uploaded_files = []
    md_file = None
    
    for file in files:
        file_path = batch_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        uploaded_files.append(file.filename)
        if file.filename.endswith('.md'):
            md_file = file.filename
    
    # Auto-detect metadata
    metadata = {}
    if md_file:
        metadata = extract_metadata_from_upload(batch_dir, md_file)
    
    return {
        "batch_id": batch_id,
        "files": uploaded_files,
        "metadata": metadata
    }


# ============================================================================
# Ingestion \u0026 Exercise Generation
# ============================================================================

def run_ingestion_task(task_id: str, file_path: str, subject_name: str, syllabus: str):
    """Background task for ingestion."""
    tasks[task_id]["status"] = "running"
    tasks[task_id]["logs"] = []
    
    try:
        # Call the ingestion script
        script_path = SCRIPTS_DIR / "auto_process_textbook.py"
        
        process = subprocess.Popen(
            ["python", str(script_path), file_path, "--subject-name", subject_name, "--syllabus", syllabus],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1, # Line buffered
            universal_newlines=True
        )
        
        # Read output line by line
        for line in iter(process.stdout.readline, ""):
            if not line:
                break
            clean_line = line.strip()
            if clean_line:
                print(f"[{task_id}] {clean_line}")
                # Store last 50 lines for the UI
                tasks[task_id]["logs"].append(clean_line)
                if len(tasks[task_id]["logs"]) > 50:
                    tasks[task_id]["logs"].pop(0)
                tasks[task_id]["message"] = clean_line # Show latest log in status
        
        process.wait()
        
        if process.returncode == 0:
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["message"] = "Ingestion completed successfully."
        else:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["message"] = f"Ingestion failed with exit code {process.returncode}."
            
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["message"] = f"Error during ingestion: {str(e)}"

@router.post("/ingest", response_model=TaskResponse)
async def trigger_ingestion(request: IngestRequest, background_tasks: BackgroundTasks):
    """Trigger the ingestion pipeline for an uploaded file."""
    print(f"DEBUG: Ingest request for batch {request.batch_id}, file {request.filename}")
    file_path = UPLOAD_DIR / request.batch_id / request.filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found in batch")
    
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "pending", "message": "Task queued"}
    
    background_tasks.add_task(
        run_ingestion_task, 
        task_id, 
        str(file_path), 
        request.subject_name, 
        request.syllabus
    )
    
    return {"task_id": task_id, "status": "pending", "message": "Ingestion started"}

def run_exercise_task(task_id: str, subtopic_id: str, generate_images: bool, count: int = 5):
    """Background task for exercise generation."""
    from .main import DB_PATH
    tasks[task_id]["status"] = "running"
    try:
        success = build_exercises_for_subtopic(
            subtopic_id, 
            generate_images=generate_images, 
            count=count,
            db_path=DB_PATH
        )
        if success:
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["message"] = f"Exercises generated for {subtopic_id}"
        else:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["message"] = f"Failed to generate exercises for {subtopic_id}"
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["message"] = f"Error: {str(e)}"

@router.post("/generate-exercises", response_model=TaskResponse)
async def generate_exercises(request: ExerciseRequest, background_tasks: BackgroundTasks):
    """Trigger exercise generation for a subtopic."""
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "pending", "message": "Task queued"}
    
    background_tasks.add_task(
        run_exercise_task,
        task_id,
        request.subtopic_id,
        request.generate_images,
        request.count
    )
    
    return {"task_id": task_id, "status": "pending", "message": "Exercise generation started"}

# ============================================================================
# Database Management
# ============================================================================

@router.delete("/db/subjects/{subject_id}", response_model=Dict[str, Any])
async def delete_subject(subject_id: str):
    """Recursively delete a subject and all its related content."""
    from .main import get_db_connection
    conn = get_db_connection()
    try:
        # Get counts for the response
        stats = conn.execute("""
            SELECT 
                (SELECT COUNT(*) FROM topics WHERE subject_id = ?) as topics,
                (SELECT COUNT(*) FROM subtopics WHERE topic_id IN (SELECT id FROM topics WHERE subject_id = ?)) as subtopics
        """, (subject_id, subject_id)).fetchone()
        
        # 1. Delete exercises
        conn.execute("""
            DELETE FROM exercises 
            WHERE subtopic_id IN (
                SELECT s.id FROM subtopics s
                JOIN topics t ON s.topic_id = t.id
                WHERE t.subject_id = ?
            )
        """, (subject_id,))
        
        # 2. Delete processed content
        conn.execute("""
            DELETE FROM content_processed 
            WHERE subtopic_id IN (
                SELECT s.id FROM subtopics s
                JOIN topics t ON s.topic_id = t.id
                WHERE t.subject_id = ?
            )
        """, (subject_id,))
        
        # 3. Delete content_raw
        conn.execute("""
            DELETE FROM content_raw 
            WHERE subtopic_id IN (
                SELECT s.id FROM subtopics s
                JOIN topics t ON s.topic_id = t.id
                WHERE t.subject_id = ?
            )
        """, (subject_id,))
        
        # 4. Delete subtopics
        conn.execute("""
            DELETE FROM subtopics 
            WHERE topic_id IN (SELECT id FROM topics WHERE subject_id = ?)
        """, (subject_id,))
        
        # 5. Delete topics
        conn.execute("DELETE FROM topics WHERE subject_id = ?", (subject_id,))
        
        # 6. Finally delete subject
        conn.execute("DELETE FROM subjects WHERE id = ?", (subject_id,))
        
        conn.commit()
        return {
            "success": True, 
            "message": f"Subject {subject_id} and all related content deleted.",
            "deleted_counts": {
                "topics": stats[0],
                "subtopics": stats[1]
            }
        }
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete subject: {str(e)}")
    finally:
        conn.close()

# ============================================================================
# Exercise CRUD Operations
# ============================================================================

@router.get("/exercises", response_model=List[Dict[str, Any]])
async def get_exercises(
    subject_id: Optional[str] = Query(None),
    topic_id: Optional[str] = Query(None),
    subtopic_id: Optional[str] = Query(None)
):
    """Get exercises filtered by subject, topic, or subtopic."""
    from .main import get_db_connection
    conn = get_db_connection()
    
    try:
        if subtopic_id:
            # Get exercises for a specific subtopic
            query = """
                SELECT e.*, s.name as subtopic_name, t.name as topic_name
                FROM exercises e
                JOIN subtopics s ON e.subtopic_id = s.id
                JOIN topics t ON s.topic_id = t.id
                WHERE e.subtopic_id = ?
                ORDER BY e.question_num
            """
            rows = conn.execute(query, (subtopic_id,)).fetchall()
        elif topic_id:
            # Get exercises for all subtopics in a topic
            query = """
                SELECT e.*, s.name as subtopic_name, t.name as topic_name
                FROM exercises e
                JOIN subtopics s ON e.subtopic_id = s.id
                JOIN topics t ON s.topic_id = t.id
                WHERE t.id = ?
                ORDER BY s.id, e.question_num
            """
            rows = conn.execute(query, (topic_id,)).fetchall()
        elif subject_id:
            # Get exercises for all subtopics in a subject
            query = """
                SELECT e.*, s.name as subtopic_name, t.name as topic_name
                FROM exercises e
                JOIN subtopics s ON e.subtopic_id = s.id
                JOIN topics t ON s.topic_id = t.id
                WHERE t.subject_id = ?
                ORDER BY t.id, s.id, e.question_num
            """
            rows = conn.execute(query, (subject_id,)).fetchall()
        else:
            # Get all exercises
            query = """
                SELECT e.*, s.name as subtopic_name, t.name as topic_name
                FROM exercises e
                JOIN subtopics s ON e.subtopic_id = s.id
                JOIN topics t ON s.topic_id = t.id
                ORDER BY t.id, s.id, e.question_num
            """
            rows = conn.execute(query).fetchall()
        
        # Convert rows to dicts and parse JSON options
        exercises = []
        for row in rows:
            exercise = dict(row)
            exercise['options'] = json.loads(exercise['options'])
            exercises.append(exercise)
        
        return exercises
    finally:
        conn.close()

@router.get("/exercises/{exercise_id}", response_model=Dict[str, Any])
async def get_exercise(exercise_id: int):
    """Get a single exercise by ID."""
    from .main import get_db_connection
    conn = get_db_connection()
    
    try:
        row = conn.execute("""
            SELECT e.*, s.name as subtopic_name, t.name as topic_name
            FROM exercises e
            JOIN subtopics s ON e.subtopic_id = s.id
            JOIN topics t ON s.topic_id = t.id
            WHERE e.id = ?
        """, (exercise_id,)).fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Exercise not found")
        
        exercise = dict(row)
        exercise['options'] = json.loads(exercise['options'])
        return exercise
    finally:
        conn.close()

@router.post("/exercises", response_model=Dict[str, Any])
async def create_exercise(request: ExerciseCreateRequest):
    """Create a new exercise."""
    from .main import get_db_connection
    conn = get_db_connection()
    
    try:
        # Validate correct_answer is in options
        if request.correct_answer not in request.options:
            raise HTTPException(
                status_code=400, 
                detail=f"Correct answer '{request.correct_answer}' not found in options"
            )
        
        # Get the next question_num for this subtopic
        max_num = conn.execute(
            "SELECT MAX(question_num) FROM exercises WHERE subtopic_id = ?",
            (request.subtopic_id,)
        ).fetchone()[0]
        next_num = (max_num or 0) + 1
        
        # Generate image if requested
        image_path = None
        if request.generate_image and request.image_prompt:
            from .exercise_builder import generate_image
            filename = f"{request.subtopic_id.replace('/', '_')}_q{next_num}.jpg"
            image_path = generate_image(request.image_prompt, filename)
        
        # Insert exercise
        cursor = conn.execute("""
            INSERT INTO exercises (
                subtopic_id, question_num, question_text, options, 
                correct_answer, explanation, image_path
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            request.subtopic_id,
            next_num,
            request.question_text,
            json.dumps(request.options),
            request.correct_answer,
            request.explanation,
            image_path
        ))
        
        conn.commit()
        exercise_id = cursor.lastrowid
        
        # Return the created exercise
        row = conn.execute(
            "SELECT * FROM exercises WHERE id = ?", 
            (exercise_id,)
        ).fetchone()
        
        exercise = dict(row)
        exercise['options'] = json.loads(exercise['options'])
        return exercise
    except sqlite3.IntegrityError as e:
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    finally:
        conn.close()

@router.put("/exercises/{exercise_id}", response_model=Dict[str, Any])
async def update_exercise(exercise_id: int, request: ExerciseUpdateRequest):
    """Update an existing exercise."""
    from .main import get_db_connection
    conn = get_db_connection()
    
    try:
        # Check if exercise exists
        existing = conn.execute(
            "SELECT * FROM exercises WHERE id = ?", 
            (exercise_id,)
        ).fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Exercise not found")
        
        # Build update query dynamically
        updates = []
        params = []
        
        if request.question_text is not None:
            updates.append("question_text = ?")
            params.append(request.question_text)
        
        if request.options is not None:
            # Validate correct_answer is in new options if provided
            correct_answer = request.correct_answer if request.correct_answer else existing['correct_answer']
            if correct_answer not in request.options:
                raise HTTPException(
                    status_code=400,
                    detail=f"Correct answer '{correct_answer}' not in options"
                )
            updates.append("options = ?")
            params.append(json.dumps(request.options))
        
        if request.correct_answer is not None:
            # Validate it's in options
            options = json.loads(existing['options']) if request.options is None else request.options
            if request.correct_answer not in options:
                raise HTTPException(
                    status_code=400,
                    detail=f"Correct answer '{request.correct_answer}' not in options"
                )
            updates.append("correct_answer = ?")
            params.append(request.correct_answer)
        
        if request.explanation is not None:
            updates.append("explanation = ?")
            params.append(request.explanation)
        
        # Generate new image if requested
        if request.generate_image and request.image_prompt:
            from .exercise_builder import generate_image
            filename = f"{existing['subtopic_id'].replace('/', '_')}_q{existing['question_num']}.jpg"
            image_path = generate_image(request.image_prompt, filename)
            if image_path:
                updates.append("image_path = ?")
                params.append(image_path)
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Execute update
        params.append(exercise_id)
        query = f"UPDATE exercises SET {', '.join(updates)} WHERE id = ?"
        conn.execute(query, params)
        conn.commit()
        
        # Return updated exercise
        row = conn.execute(
            "SELECT * FROM exercises WHERE id = ?",
            (exercise_id,)
        ).fetchone()
        
        exercise = dict(row)
        exercise['options'] = json.loads(exercise['options'])
        return exercise
    finally:
        conn.close()

@router.delete("/exercises/{exercise_id}", response_model=Dict[str, Any])
async def delete_exercise(exercise_id: int):
    """Delete an exercise."""
    from .main import get_db_connection
    conn = get_db_connection()
    
    try:
        # Check if exists
        existing = conn.execute(
            "SELECT * FROM exercises WHERE id = ?",
            (exercise_id,)
        ).fetchone()
        
        if not existing:
            raise HTTPException(status_code=404, detail="Exercise not found")
        
        # Delete
        conn.execute("DELETE FROM exercises WHERE id = ?", (exercise_id,))
        conn.commit()
        
        return {
            "success": True,
            "message": f"Exercise {exercise_id} deleted successfully"
        }
    finally:
        conn.close()

@router.delete("/exercises", response_model=Dict[str, Any])
async def delete_exercises_bulk(subtopic_id: str = Query(...)):
    """Delete all exercises for a subtopic."""
    from .main import get_db_connection
    conn = get_db_connection()
    
    try:
        # Get count
        count = conn.execute(
            "SELECT COUNT(*) FROM exercises WHERE subtopic_id = ?",
            (subtopic_id,)
        ).fetchone()[0]
        
        # Delete
        conn.execute("DELETE FROM exercises WHERE subtopic_id = ?", (subtopic_id,))
        conn.commit()
        
        return {
            "success": True,
            "message": f"Deleted {count} exercises for subtopic {subtopic_id}",
            "deleted_count": count
        }
    finally:
        conn.close()

@router.post("/exercises/reorder", response_model=Dict[str, Any])
async def reorder_exercises(subtopic_id: str, exercise_ids: List[int]):
    """Reorder exercises for a subtopic by providing ordered list of IDs."""
    from .main import get_db_connection
    conn = get_db_connection()
    
    try:
        # Verify all IDs belong to the subtopic
        existing = conn.execute(
            "SELECT id FROM exercises WHERE subtopic_id = ? ORDER BY question_num",
            (subtopic_id,)
        ).fetchall()
        existing_ids = {row[0] for row in existing}
        
        if set(exercise_ids) != existing_ids:
            raise HTTPException(
                status_code=400,
                detail="Provided IDs don't match existing exercises for this subtopic"
            )
        
        # Update question_num for each exercise
        for new_num, exercise_id in enumerate(exercise_ids, 1):
            conn.execute(
                "UPDATE exercises SET question_num = ? WHERE id = ?",
                (new_num, exercise_id)
            )
        
        conn.commit()
        
        return {
            "success": True,
            "message": f"Reordered {len(exercise_ids)} exercises"
        }
    finally:
        conn.close()

# ============================================================================
# Task Management
# ============================================================================

@router.get("/tasks", response_model=Dict[str, Dict])
async def get_tasks():
    """Get status of all tasks."""
    return tasks

@router.get("/tasks/{task_id}", response_model=Dict)
async def get_task_status(task_id: str):
    """Get status of a specific task."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]
