from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.services.pdf_service import pdf_service
from backend.services.gemini_service import gemini_service
from backend.core.config import settings
from backend.database import get_db
from backend.models.quiz import Material
import os
import shutil
import uuid
from typing import Optional
import os
import requests
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form, Header

router = APIRouter()
SUGARCLASS_API_URL = os.getenv("SUGARCLASS_API_URL", "http://backend:8000/api/v1")

def report_activity(service: str, activity_type: str, token: str, metadata: dict = None, score: int = 100):
    if not token:
        return
    try:
        requests.post(
            f"{SUGARCLASS_API_URL}/progress/",
            json={
                "service": service,
                "activity_type": activity_type,
                "metadata_json": metadata or {},
                "score": score
            },
            headers={"Authorization": token},
            timeout=2
        )
    except Exception as e:
        print(f"Failed to report activity: {e}")

@router.post("/")
async def upload_material(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    if not file.filename.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="Unsupported file format")
    
    file_id = str(uuid.uuid4())
    extension = os.path.splitext(file.filename)[1]
    file_path = os.path.join(settings.UPLOAD_DIR, f"{file_id}{extension}")
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Extract text
    text = ""
    if extension.lower() == '.pdf':
        text = await pdf_service.extract_text(file_path)
    else:
        text = await gemini_service.extract_text_from_image(file_path)
    
    # Save to database
    material = Material(
        id=file_id,
        filename=file.filename,
        file_path=file_path,
        extracted_text=text,
        session_id=session_id
    )
    db.add(material)
    await db.commit()

    # Report to Sugarclass Shell
    if authorization:
        report_activity(
            service="examiner",
            activity_type="material_upload",
            token=authorization,
            metadata={"material_id": file_id, "filename": file.filename}
        )
        
    return {
        "id": file_id,
        "filename": file.filename,
        "text_preview": text[:500] + "..." if len(text) > 500 else text,
        "full_text": text
    }

@router.get("/")
async def get_materials(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Material).order_by(Material.created_at.desc()))
    materials = result.scalars().all()
    return materials

@router.get("/start-session")
async def start_upload_session():
    session_id = str(uuid.uuid4())
    from backend.services.mobile_service import mobile_service
    qr_code = mobile_service.generate_qr_for_session(session_id)
    return {
        "session_id": session_id,
        "qr_code": f"data:image/png;base64,{qr_code}"
    }

@router.get("/session/{session_id}")
async def get_upload_session(session_id: str, db: AsyncSession = Depends(get_db)):
    # Check if any material has been uploaded for this session
    result = await db.execute(select(Material).where(Material.session_id == session_id))
    materials = result.scalars().all()
    if materials:
        return {"session_id": session_id, "status": "completed", "materials": materials}
    return {"session_id": session_id, "status": "active"}

@router.delete("/{material_id}")
async def delete_material(material_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Delete file
    if os.path.exists(material.file_path):
        os.remove(material.file_path)
        
    await db.delete(material)
    await db.commit()
    return {"status": "success"}
