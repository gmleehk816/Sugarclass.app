from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
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


def extract_metadata_from_upload(batch_dir: Path, md_filename: str) -> Dict[str, Optional[str]]:
    """
    Extract subject name and syllabus from uploaded files.
    
    Priority for subject name:
    1. .structure.json file (if present)
    2. First H1 heading (# Title) in markdown
    3. Cleaned filename
    
    Priority for syllabus:
    1. .structure.json file (if present)
    2. Default to None (user must specify)
    """
    result = {"subject_name": None, "syllabus": None}
    
    # Check for .structure.json
    for json_file in batch_dir.glob("*.structure.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                structure = json.load(f)
                if "subject_name" in structure:
                    result["subject_name"] = structure["subject_name"]
                if "syllabus" in structure:
                    result["syllabus"] = structure["syllabus"]
                return result
        except (json.JSONDecodeError, IOError):
            pass
    
    # Try to extract from markdown file
    md_path = batch_dir / md_filename
    if md_path.exists():
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                # Read first 50 lines to find H1
                for i, line in enumerate(f):
                    if i > 50:
                        break
                    line = line.strip()
                    # Look for H1 heading: # Title
                    if line.startswith("# ") and not line.startswith("## "):
                        result["subject_name"] = line[2:].strip()
                        break
        except IOError:
            pass
    
    # Fallback: clean up filename
    if not result["subject_name"] and md_filename:
        # Remove extension and clean up
        name = md_filename.replace(".md", "")
        # Replace underscores and hyphens with spaces
        name = name.replace("_", " ").replace("-", " ")
        # Title case
        name = name.title()
        result["subject_name"] = name
    
    return result


@router.post("/upload", response_model=Dict[str, Any])
async def upload_files(files: List[UploadFile] = File(...)):
    """Upload one or more files for processing as a batch."""
    print(f"DEBUG: Received upload request for {len(files)} files")
    batch_id = str(uuid.uuid4())
    batch_dir = UPLOAD_DIR / batch_id
    batch_dir.mkdir(parents=True, exist_ok=True)
    
    uploaded_files = []
    main_markdown = ""
    
    for file in files:
        file_path = batch_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        uploaded_files.append(file.filename)
        if file.filename.endswith(".md"):
            main_markdown = file.filename
    
    # Extract metadata from uploaded files
    metadata = extract_metadata_from_upload(batch_dir, main_markdown)
            
    return {
        "batch_id": batch_id, 
        "files": uploaded_files,
        "main_markdown": main_markdown,
        "suggested_subject": metadata["subject_name"],
        "suggested_syllabus": metadata["syllabus"]
    }

def run_ingestion_task(task_id: str, file_path: str, subject_name: str, syllabus: str):
    """Background task for ingestion with live log streaming."""
    tasks[task_id]["status"] = "running"
    tasks[task_id]["logs"] = []
    
    try:
        cmd = [
            "python", "-u", str(SCRIPTS_DIR / "auto_process_textbook.py"),
            file_path,
            "--subject-name", subject_name,
            "--syllabus", syllabus
        ]
        
        # Start process with unbuffered output (-u)
        process = subprocess.Popen(
            cmd,
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

def run_exercise_task(task_id: str, subtopic_id: str, generate_images: bool):
    """Background task for exercise generation."""
    tasks[task_id]["status"] = "running"
    try:
        success = build_exercises_for_subtopic(subtopic_id, generate_images=generate_images)
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
        request.generate_images
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
