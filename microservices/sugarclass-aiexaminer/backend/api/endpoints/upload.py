from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.services.pdf_service import pdf_service, MAX_PAGES_LIMIT
from backend.services.gemini_service import gemini_service
from backend.core.config import settings
from backend.database import get_db
from backend.models.quiz import Material
import os
import shutil
import uuid
from typing import Optional, List
import requests
from pydantic import BaseModel

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


class PageSelectionRequest(BaseModel):
    material_id: str
    selected_pages: List[int]


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
    
    is_pdf = extension.lower() == '.pdf'
    total_pages = 0
    requires_page_selection = False
    
    # For PDFs, check page count first
    if is_pdf:
        total_pages = await pdf_service.get_page_count(file_path)
        requires_page_selection = total_pages > MAX_PAGES_LIMIT
    
    # Extract text (with page limit for large PDFs)
    text = ""
    processed_pages = []
    if is_pdf:
        if requires_page_selection:
            # Don't extract text yet - user needs to select pages first
            text = ""
            processed_pages = []
        else:
            text, _, processed_pages = await pdf_service.extract_text_with_metadata(file_path)
    else:
        text = await gemini_service.extract_text_from_image(file_path)
        total_pages = 1
        processed_pages = [1]
    
    # Get page previews for page selection UI
    page_previews = []
    if requires_page_selection:
        page_previews = await pdf_service.get_page_previews(file_path)
    
    # Save to database with page info
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
            metadata={"material_id": file_id, "filename": file.filename, "total_pages": total_pages}
        )
        
    return {
        "id": file_id,
        "filename": file.filename,
        "text_preview": text[:500] + "..." if len(text) > 500 else text,
        "full_text": text,
        "total_pages": total_pages,
        "processed_pages": processed_pages,
        "requires_page_selection": requires_page_selection,
        "max_pages_limit": MAX_PAGES_LIMIT,
        "page_previews": page_previews
    }


@router.post("/process-pages")
async def process_selected_pages(
    request: PageSelectionRequest,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Process a PDF with user-selected pages (max 20)"""
    # Get material
    result = await db.execute(select(Material).where(Material.id == request.material_id))
    material = result.scalar_one_or_none()
    
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    if not material.file_path.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Page selection only applies to PDF files")
    
    # Validate page selection
    if len(request.selected_pages) > MAX_PAGES_LIMIT:
        raise HTTPException(
            status_code=400, 
            detail=f"Maximum {MAX_PAGES_LIMIT} pages can be selected"
        )
    
    if len(request.selected_pages) == 0:
        raise HTTPException(status_code=400, detail="At least one page must be selected")
    
    # Extract text from selected pages
    text, total_pages, processed_pages = await pdf_service.extract_text_with_metadata(
        material.file_path, 
        request.selected_pages
    )
    
    # Update material with extracted text
    material.extracted_text = text
    await db.commit()
    
    if authorization:
        report_activity(
            service="examiner",
            activity_type="page_selection",
            token=authorization,
            metadata={
                "material_id": request.material_id, 
                "selected_pages": processed_pages,
                "total_pages": total_pages
            }
        )
    
    return {
        "id": request.material_id,
        "filename": material.filename,
        "text_preview": text[:500] + "..." if len(text) > 500 else text,
        "full_text": text,
        "total_pages": total_pages,
        "processed_pages": processed_pages,
        "requires_page_selection": False
    }


@router.get("/pdf-info/{material_id}")
async def get_pdf_info(material_id: str, db: AsyncSession = Depends(get_db)):
    """Get PDF page information for page selection UI"""
    result = await db.execute(select(Material).where(Material.id == material_id))
    material = result.scalar_one_or_none()
    
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    if not material.file_path.lower().endswith('.pdf'):
        return {
            "material_id": material_id,
            "filename": material.filename,
            "is_pdf": False,
            "total_pages": 1,
            "max_pages_limit": MAX_PAGES_LIMIT
        }
    
    total_pages = await pdf_service.get_page_count(material.file_path)
    
    return {
        "material_id": material_id,
        "filename": material.filename,
        "is_pdf": True,
        "total_pages": total_pages,
        "max_pages_limit": MAX_PAGES_LIMIT,
        "requires_page_selection": total_pages > MAX_PAGES_LIMIT
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

