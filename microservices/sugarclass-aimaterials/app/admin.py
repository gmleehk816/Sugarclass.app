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

class SubjectRenameRequest(BaseModel):
    name: str

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

@router.patch("/db/subjects/{subject_id}", response_model=Dict[str, Any])
async def rename_subject(subject_id: str, request: SubjectRenameRequest):
    """Rename a subject."""
    from .main import get_db_connection
    conn = get_db_connection()
    try:
        # Check if subject exists
        subject = conn.execute("SELECT name FROM subjects WHERE id = ?", (subject_id,)).fetchone()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")
        
        old_name = subject[0]
        new_name = request.name.strip()
        
        if not new_name:
            raise HTTPException(status_code=400, detail="Name cannot be empty")
            
        conn.execute("UPDATE subjects SET name = ? WHERE id = ?", (new_name, subject_id))
        conn.commit()
        
        return {
            "success": True,
            "message": f"Subject renamed from '{old_name}' to '{new_name}'",
            "subject_id": subject_id,
            "new_name": new_name
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to rename subject: {str(e)}")
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

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Dismiss/delete a task from the monitor."""
    if task_id in tasks:
        del tasks[task_id]
        return {"success": True, "message": f"Task {task_id} dismissed"}
    raise HTTPException(status_code=404, detail="Task not found")

# ============================================================================
# Content Image Generation
# ============================================================================

class ContentImageRequest(BaseModel):
    """Request model for generating a content image."""
    prompt: str

def _generate_single_image_internal(prompt: str) -> Dict[str, Any]:
    """Internal helper to generate an image and return URL/filename."""
    import requests as http_requests
    from io import BytesIO
    from PIL import Image
    import re
    import uuid
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
            import time
            time.sleep(2)

        if img_response and img_response.status_code == 200:
            gen_images_dir = BASE_DIR / "generated_images"
            gen_images_dir.mkdir(parents=True, exist_ok=True)

            filename = f"content_{uuid.uuid4().hex[:12]}.jpg"
            img_path = gen_images_dir / filename

            img = Image.open(BytesIO(img_response.content))
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
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

def _generate_images_for_content(html_content: str, subtopic_id: str, conn, add_log):
    """Parses HTML for [GENERATE_IMAGE: prompt] markers and replaces them with images."""
    import re
    
    # regex to find [GENERATE_IMAGE: some descriptive prompt]
    marker_pattern = r'\[GENERATE_IMAGE:\s*(.*?)\]'
    markers = re.findall(marker_pattern, html_content)
    
    if not markers:
        add_log("No image markers found in content, using fallback (headings)...")
        # Fallback to old behavior if no markers found
        headings = re.findall(r'<(h[1-3])[^>]*>(.*?)</\1>', html_content, re.IGNORECASE | re.DOTALL)
        if not headings:
            add_log("No headings found either, skipping image generation.")
            return html_content
        
        # Limit to 2 fallback images to be safe
        markers = [re.sub(r'<[^>]+>', '', h[1]).strip() for h in headings[:2]]
        is_fallback = True
    else:
        is_fallback = False
        add_log(f"Found {len(markers)} intentional image markers from AI.")

        # Limit AI markers to 5 to avoid infinite generation loops/costs
        if len(markers) > 5:
            add_log("Too many markers found, limiting to first 5.")
            markers = markers[:5]

    new_html = html_content
    processed_count = 0

    for prompt in markers:
        if len(prompt) < 3:
            continue
            
        try:
            add_log(f"Generating image for: '{prompt}'...")
            res = _generate_single_image_internal(prompt)
            
            if res["success"]:
                img_url = res["image_url"]
                image_html = f'<figure style="text-align:center;margin:24px 0;"><img src="{img_url}" alt="{prompt}" style="max-width:100%;border-radius:16px;box-shadow:0 8px 30px rgba(0,0,0,0.12);"/><figcaption style="margin-top:12px;font-size:0.9rem;color:#64748b;font-style:italic;max-width:80%;margin-left:auto;margin-right:auto;">{prompt}</figcaption></figure>'
                
                if is_fallback:
                    # Old logic: Find the heading and insert after it
                    # We need to find the heading that matched this prompt
                    # This is slightly complex in fallback mode, so we just replace the first Match
                    pattern = r'<(h[1-3])[^>]*>.*?' + re.escape(prompt) + r'.*?</\1>'
                    new_html = re.sub(pattern, lambda m: m.group(0) + '\n' + image_html, new_html, count=1, flags=re.IGNORECASE | re.DOTALL)
                else:
                    # New logic: Replace the marker exactly
                    # Escaping the specific marker to be safe
                    specific_marker = f'[GENERATE_IMAGE: {prompt}]'
                    # Handle cases where AI might have slightly different spacing
                    esc_prompt = re.escape(prompt)
                    marker_regex = r'\[GENERATE_IMAGE:\s*' + esc_prompt + r'\s*\]'
                    new_html = re.sub(marker_regex, image_html, new_html, count=1)
                
                processed_count += 1
                add_log(f"✅ Image {processed_count} generated and inserted.")
        except Exception as e:
            add_log(f"⚠️ Failed to generate image for '{prompt}': {str(e)}")

    # Cleanup any remaining markers if AI went crazy
    new_html = re.sub(marker_pattern, '', new_html)

    # Update database with the new HTML containing images
    if processed_count > 0:
        add_log(f"Updating database with {processed_count} images inserted.")
        conn.execute("UPDATE content_processed SET html_content = ? WHERE subtopic_id = ?", (new_html, subtopic_id))
        conn.commit()
    
    return new_html

@router.post("/generate-content-image", response_model=Dict[str, Any])
async def generate_content_image(request: ContentImageRequest):
    """Generate an image using grok-image-1.0 and return its URL."""
    try:
        res = _generate_single_image_internal(request.prompt)
        return res
    except Exception as e:
        if "not configured" in str(e):
            raise HTTPException(status_code=500, detail=str(e))
        raise HTTPException(status_code=502, detail=str(e))

# ============================================================================
# Content CRUD Operations
# ============================================================================

class ContentUpdateRequest(BaseModel):
    """Request model for updating processed content."""
    html_content: str
    summary: Optional[str] = None
    key_terms: Optional[str] = None

class ContentRegenerateRequest(BaseModel):
    """Request model for regenerating content with options."""
    focus: Optional[str] = None  # e.g., "more creative", "focus on examples", "simpler"
    temperature: Optional[float] = 0.7  # Creativity level
    include_key_terms: bool = True
    include_summary: bool = True
    include_think_about_it: bool = True
    generate_images: bool = False
    generate_videos: bool = False  # placeholder for future
    custom_prompt: Optional[str] = None # User's additional instructions

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


@router.get("/contents", response_model=List[Dict[str, Any]])
async def get_contents(
    subject_id: Optional[str] = Query(None),
    topic_id: Optional[str] = Query(None),
    subtopic_id: Optional[str] = Query(None),
    include_raw: bool = False
):
    """Get processed content filtered by subject, topic, or subtopic."""
    from .main import get_db_connection
    conn = get_db_connection()

    try:
        if subtopic_id:
            query = """
                SELECT cp.*, s.name as subtopic_name, t.name as topic_name, sub.name as subject_name
                FROM content_processed cp
                JOIN subtopics s ON cp.subtopic_id = s.id
                JOIN topics t ON s.topic_id = t.id
                JOIN subjects sub ON t.subject_id = sub.id
                WHERE cp.subtopic_id = ?
                ORDER BY s.order_num
            """
            rows = conn.execute(query, (subtopic_id,)).fetchall()
        elif topic_id:
            query = """
                SELECT cp.*, s.name as subtopic_name, t.name as topic_name, sub.name as subject_name
                FROM content_processed cp
                JOIN subtopics s ON cp.subtopic_id = s.id
                JOIN topics t ON s.topic_id = t.id
                JOIN subjects sub ON t.subject_id = sub.id
                WHERE t.id = ?
                ORDER BY s.order_num
            """
            rows = conn.execute(query, (topic_id,)).fetchall()
        elif subject_id:
            query = """
                SELECT cp.*, s.name as subtopic_name, t.name as topic_name, sub.name as subject_name
                FROM content_processed cp
                JOIN subtopics s ON cp.subtopic_id = s.id
                JOIN topics t ON s.topic_id = t.id
                JOIN subjects sub ON t.subject_id = sub.id
                WHERE t.subject_id = ?
                ORDER BY sub.name, t.name, s.order_num
            """
            rows = conn.execute(query, (subject_id,)).fetchall()
        else:
            query = """
                SELECT cp.*, s.name as subtopic_name, t.name as topic_name, sub.name as subject_name
                FROM content_processed cp
                JOIN subtopics s ON cp.subtopic_id = s.id
                JOIN topics t ON s.topic_id = t.id
                JOIN subjects sub ON t.subject_id = sub.id
                ORDER BY sub.name, t.name, s.order_num
            """
            rows = conn.execute(query).fetchall()

        contents = []
        for row in rows:
            content = dict(row)
            # Optionally include raw content
            if include_raw and content.get('raw_id'):
                raw = conn.execute(
                    "SELECT markdown_content FROM content_raw WHERE id = ?",
                    (content['raw_id'],)
                ).fetchone()
                if raw:
                    content['markdown_content'] = raw['markdown_content']
            contents.append(content)

        return contents
    finally:
        conn.close()

@router.get("/contents/{content_id}", response_model=Dict[str, Any])
async def get_content(content_id: int, include_raw: bool = False):
    """Get a single processed content by ID."""
    from .main import get_db_connection
    conn = get_db_connection()

    try:
        row = conn.execute("""
            SELECT cp.*, s.name as subtopic_name, t.name as topic_name, sub.name as subject_name
            FROM content_processed cp
            JOIN subtopics s ON cp.subtopic_id = s.id
            JOIN topics t ON s.topic_id = t.id
            JOIN subjects sub ON t.subject_id = sub.id
            WHERE cp.id = ?
        """, (content_id,)).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Content not found")

        content = dict(row)

        # Include raw content if requested
        if include_raw and content.get('raw_id'):
            raw = conn.execute(
                "SELECT markdown_content, title FROM content_raw WHERE id = ?",
                (content['raw_id'],)
            ).fetchone()
            if raw:
                content['markdown_content'] = raw['markdown_content']
                content['raw_title'] = raw['title']

        return content
    finally:
        conn.close()

@router.get("/contents/subtopic/{subtopic_id}", response_model=Dict[str, Any])
async def get_content_by_subtopic(subtopic_id: str, include_raw: bool = False):
    """Get processed content for a specific subtopic."""
    from .main import get_db_connection
    conn = get_db_connection()

    try:
        row = conn.execute("""
            SELECT cp.*, s.name as subtopic_name, t.name as topic_name, sub.name as subject_name
            FROM content_processed cp
            JOIN subtopics s ON cp.subtopic_id = s.id
            JOIN topics t ON s.topic_id = t.id
            JOIN subjects sub ON t.subject_id = sub.id
            WHERE cp.subtopic_id = ?
        """, (subtopic_id,)).fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Content not found for this subtopic")

        content = dict(row)

        # Include raw content if requested
        if include_raw and content.get('raw_id'):
            raw = conn.execute(
                "SELECT markdown_content, title FROM content_raw WHERE id = ?",
                (content['raw_id'],)
            ).fetchone()
            if raw:
                content['markdown_content'] = raw['markdown_content']
                content['raw_title'] = raw['title']

        return content
    finally:
        conn.close()

@router.put("/contents/{content_id}", response_model=Dict[str, Any])
async def update_content(content_id: int, request: ContentUpdateRequest):
    """Update processed content (html_content, summary, key_terms)."""
    from .main import get_db_connection
    conn = get_db_connection()

    try:
        # Check if content exists
        existing = conn.execute(
            "SELECT * FROM content_processed WHERE id = ?",
            (content_id,)
        ).fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Content not found")

        # Update processed content
        conn.execute("""
            UPDATE content_processed
            SET html_content = ?,
                summary = COALESCE(?, summary),
                key_terms = COALESCE(?, key_terms),
                processor_version = 'manual_edit',
                processed_at = datetime('now')
            WHERE id = ?
        """, (request.html_content, request.summary, request.key_terms, content_id))

        conn.commit()

        # Return updated content
        row = conn.execute("""
            SELECT cp.*, s.name as subtopic_name, t.name as topic_name, sub.name as subject_name
            FROM content_processed cp
            JOIN subtopics s ON cp.subtopic_id = s.id
            JOIN topics t ON s.topic_id = t.id
            JOIN subjects sub ON t.subject_id = sub.id
            WHERE cp.id = ?
        """, (content_id,)).fetchone()

        return dict(row)
    finally:
        conn.close()

@router.delete("/contents/{content_id}", response_model=Dict[str, Any])
async def delete_content(content_id: int):
    """Delete processed content only (keeps raw content for re-processing)."""
    from .main import get_db_connection
    conn = get_db_connection()

    try:
        # Check if content exists
        existing = conn.execute(
            "SELECT id, subtopic_id FROM content_processed WHERE id = ?",
            (content_id,)
        ).fetchone()

        if not existing:
            raise HTTPException(status_code=404, detail="Content not found")

        subtopic_id = existing['subtopic_id']

        # Delete only from content_processed (raw content is preserved)
        conn.execute("DELETE FROM content_processed WHERE id = ?", (content_id,))
        conn.commit()

        return {
            "success": True,
            "message": f"Content {content_id} deleted. Raw content preserved for re-processing.",
            "subtopic_id": subtopic_id
        }
    finally:
        conn.close()

@router.delete("/contents", response_model=Dict[str, Any])
async def delete_contents_bulk(subtopic_id: str = Query(...)):
    """Delete all processed content for a subtopic (keeps raw content)."""
    from .main import get_db_connection
    conn = get_db_connection()

    try:
        # Get count
        count = conn.execute(
            "SELECT COUNT(*) FROM content_processed WHERE subtopic_id = ?",
            (subtopic_id,)
        ).fetchone()[0]

        # Delete only from content_processed
        conn.execute("DELETE FROM content_processed WHERE subtopic_id = ?", (subtopic_id,))
        conn.commit()

        return {
            "success": True,
            "message": f"Deleted {count} processed contents for subtopic {subtopic_id}. Raw content preserved.",
            "deleted_count": count
        }
    finally:
        conn.close()

def run_content_regenerate_task(
    task_id: str,
    subtopic_id: str,
    focus: Optional[str],
    temperature: float,
    include_key_terms: bool,
    include_summary: bool,
    include_think_about_it: bool,
    generate_images: bool = False,
    custom_prompt: Optional[str] = None
):
    """Background task for content regeneration with options."""
    from .main import DB_PATH, get_db_connection
    import markdown

    tasks[task_id]["status"] = "running"
    tasks[task_id]["logs"] = []

    def add_log(message: str):
        print(f"[{task_id}] {message}")
        tasks[task_id]["logs"].append(message)
        if len(tasks[task_id]["logs"]) > 50:
            tasks[task_id]["logs"].pop(0)
        tasks[task_id]["message"] = message

    try:
        conn = get_db_connection()

        # Get raw content
        add_log("Fetching raw content...")
        raw_row = conn.execute("""
            SELECT cr.id, cr.markdown_content, cr.title, cr.subtopic_id
            FROM content_raw cr
            WHERE cr.subtopic_id = ?
            ORDER BY cr.id DESC
            LIMIT 1
        """, (subtopic_id,)).fetchone()

        if not raw_row:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["message"] = f"No raw content found for subtopic {subtopic_id}"
            return

        markdown_content = raw_row['markdown_content']

        # Check if there's already a processed entry
        existing = conn.execute(
            "SELECT id FROM content_processed WHERE subtopic_id = ?",
            (subtopic_id,)
        ).fetchone()

        # Convert markdown to HTML
        add_log("Converting markdown to HTML...")
        html_content = markdown.markdown(
            markdown_content,
            extensions=['tables', 'fenced_code', 'nl2br', 'sane_lists']
        )

        # Build system prompt based on focus
        system_prompt = "You are an expert educational content enhancer."
        if focus:
            system_prompt += f" Focus: {focus}."

        # Build user prompt with sections
        user_prompt = f"""Enhance the following educational content in HTML format.

{f"Make it more creative and engaging." if temperature > 0.7 else f"Keep it clear and concise." if temperature < 0.5 else ""}

{"Include key terms with definitions." if include_key_terms else ""}

{"Include a summary section." if include_summary else ""}

{"Include 'Think About It' reflection questions." if include_think_about_it else ""}

{f"ADDITIONAL INSTRUCTIONS: {custom_prompt}" if custom_prompt else ""}

Return the enhanced HTML content wrapped in ```html``` code blocks.
Do NOT include the original markdown - return only the enhanced HTML.

IMPORTANT (IMAGE PLACEMENT):
If "Generate Images" is requested, you MUST identify 2-3 optimal locations in the content where an illustrative image would be helpful. At these locations, insert the marker [GENERATE_IMAGE: descriptive prompt for the image].
The prompt should be a detailed description of what the image should show to explain the surrounding text. Do NOT place images too close together.

Original HTML content:
{html_content}"""

        add_log(f"Calling LLM with temperature={temperature}...")

        # Use OpenAI client for content generation
        from openai import OpenAI
        from .config_fastapi import settings

        if not settings.LLM_API_KEY:
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["message"] = "LLM_API_KEY not configured"
            return

        client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_API_URL
        )

        try:
            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature
            )

            llm_result = response.choices[0].message

            if llm_result and llm_result.content:
                # Extract HTML from code blocks if present
                enhanced_html = llm_result.content

                enhanced_html = enhanced_html.strip()

                # NEW: Clean up HTML to prevent global style leaks
                # 1. Extract body content if present
                body_match = re.search(r'<body[^>]*>(.*?)</body>', enhanced_html, re.DOTALL | re.IGNORECASE)
                if body_match:
                    enhanced_html = body_match.group(1)
                
                # 2. Strip ALL <style> tags (they cause layout issues when inlined)
                enhanced_html = re.sub(r'<style[^>]*>.*?</style>', '', enhanced_html, flags=re.DOTALL | re.IGNORECASE)
                
                # 3. Strip <html> and <head> tags if they still exist
                enhanced_html = re.sub(r'<html[^>]*>|</html>|<head[^>]*>.*?</head>|<!DOCTYPE[^>]*>', '', enhanced_html, flags=re.DOTALL | re.IGNORECASE)
                
                enhanced_html = enhanced_html.strip()

                add_log("Saving enhanced content...")

                if existing:
                    # Update existing
                    conn.execute("""
                        UPDATE content_processed
                        SET html_content = ?,
                            processor_version = ?,
                            processed_at = datetime('now')
                        WHERE id = ?
                    """, (enhanced_html, f'llm_regenerate_{focus or "default"}', existing['id']))
                else:
                    # Insert new
                    conn.execute("""
                        INSERT INTO content_processed (
                            raw_id, subtopic_id, html_content, processor_version
                        ) VALUES (?, ?, ?, ?)
                    """, (raw_row['id'], subtopic_id, enhanced_html, f'llm_regenerate_{focus or "default"}'))

                conn.commit()
                add_log("Content regeneration completed successfully!")

                # --- Generate images for headings if requested ---
                if generate_images:
                    add_log("Generating images for content sections...")
                    try:
                        _generate_images_for_content(enhanced_html, subtopic_id, conn, add_log)
                    except Exception as img_err:
                        add_log(f"Image generation had errors (content still saved): {str(img_err)}")

                tasks[task_id]["status"] = "completed"
                tasks[task_id]["message"] = "Content regenerated successfully"
            else:
                tasks[task_id]["status"] = "failed"
                tasks[task_id]["message"] = "LLM returned no content"

        except Exception as llm_error:
            add_log(f"LLM API error: {str(llm_error)}")
            tasks[task_id]["status"] = "failed"
            tasks[task_id]["message"] = f"LLM API error: {str(llm_error)}"

    except Exception as e:
        add_log(f"Error: {str(e)}")
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["message"] = f"Error: {str(e)}"
    finally:
        conn.close()

@router.post("/contents/regenerate", response_model=TaskResponse)
async def regenerate_content(
    request: ContentRegenerateRequest,
    background_tasks: BackgroundTasks,
    subtopic_id: str = Query(...)
):
    """Regenerate content with AI using specified options."""
    # Get the subtopic_id from query parameter
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "pending", "message": "Regeneration queued", "logs": []}

    background_tasks.add_task(
        run_content_regenerate_task,
        task_id,
        subtopic_id,
        request.focus,
        request.temperature or 0.7,
        request.include_key_terms,
        request.include_summary,
        request.include_think_about_it,
        request.generate_images,
        request.custom_prompt
    )

    return {"task_id": task_id, "status": "pending", "message": "Content regeneration started"}
