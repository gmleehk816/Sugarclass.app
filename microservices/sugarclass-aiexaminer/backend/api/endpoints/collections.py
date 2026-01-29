from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from backend.database import get_db
from backend.models.quiz import Collection, Material
from pydantic import BaseModel
from typing import Optional, List
import os

router = APIRouter()


class CollectionCreate(BaseModel):
    name: str
    description: Optional[str] = None


class CollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class MaterialAddToCollection(BaseModel):
    material_id: str
    collection_id: str


@router.post("/")
async def create_collection(request: CollectionCreate, db: AsyncSession = Depends(get_db)):
    """Create a new collection/folder"""
    collection = Collection(
        name=request.name,
        description=request.description
    )
    db.add(collection)
    await db.commit()
    await db.refresh(collection)
    return collection


@router.get("/")
async def get_collections(db: AsyncSession = Depends(get_db)):
    """Get all collections with their materials"""
    result = await db.execute(select(Collection).order_by(Collection.created_at.desc()))
    collections = result.scalars().all()
    
    # Get materials for each collection
    collections_with_materials = []
    for collection in collections:
        materials_result = await db.execute(
            select(Material).where(Material.collection_id == collection.id)
        )
        materials = materials_result.scalars().all()
        collections_with_materials.append({
            "id": collection.id,
            "name": collection.name,
            "description": collection.description,
            "created_at": collection.created_at,
            "updated_at": collection.updated_at,
            "materials": materials,
            "material_count": len(materials)
        })
    
    return collections_with_materials


@router.get("/{collection_id}")
async def get_collection(collection_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific collection with its materials"""
    result = await db.execute(select(Collection).where(Collection.id == collection_id))
    collection = result.scalar_one_or_none()
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Get materials in this collection
    materials_result = await db.execute(
        select(Material).where(Material.collection_id == collection_id)
    )
    materials = materials_result.scalars().all()
    
    return {
        "id": collection.id,
        "name": collection.name,
        "description": collection.description,
        "created_at": collection.created_at,
        "updated_at": collection.updated_at,
        "materials": materials
    }


@router.patch("/{collection_id}")
async def update_collection(
    collection_id: str,
    request: CollectionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update collection name/description"""
    result = await db.execute(select(Collection).where(Collection.id == collection_id))
    collection = result.scalar_one_or_none()
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    if request.name is not None:
        collection.name = request.name
    if request.description is not None:
        collection.description = request.description
    
    await db.commit()
    await db.refresh(collection)
    return collection


@router.delete("/{collection_id}")
async def delete_collection(collection_id: str, db: AsyncSession = Depends(get_db)):
    """Delete a collection and optionally its materials"""
    result = await db.execute(select(Collection).where(Collection.id == collection_id))
    collection = result.scalar_one_or_none()
    
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Get all materials in this collection
    materials_result = await db.execute(
        select(Material).where(Material.collection_id == collection_id)
    )
    materials = materials_result.scalars().all()
    
    # Delete physical files and material records
    for material in materials:
        if os.path.exists(material.file_path):
            os.remove(material.file_path)
        await db.delete(material)
    
    # Delete the collection
    await db.delete(collection)
    await db.commit()
    
    return {"status": "success", "deleted_materials": len(materials)}


@router.post("/add-material")
async def add_material_to_collection(
    request: MaterialAddToCollection,
    db: AsyncSession = Depends(get_db)
):
    """Add an existing material to a collection"""
    # Check if collection exists
    collection_result = await db.execute(
        select(Collection).where(Collection.id == request.collection_id)
    )
    collection = collection_result.scalar_one_or_none()
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Check if material exists
    material_result = await db.execute(
        select(Material).where(Material.id == request.material_id)
    )
    material = material_result.scalar_one_or_none()
    if not material:
        raise HTTPException(status_code=404, detail="Material not found")
    
    # Add material to collection
    material.collection_id = request.collection_id
    await db.commit()
    await db.refresh(material)
    
    return {"status": "success", "material": material}


@router.post("/{collection_id}/remove-material/{material_id}")
async def remove_material_from_collection(
    collection_id: str,
    material_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Remove a material from a collection (doesn't delete the material)"""
    material_result = await db.execute(
        select(Material).where(
            Material.id == material_id,
            Material.collection_id == collection_id
        )
    )
    material = material_result.scalar_one_or_none()
    
    if not material:
        raise HTTPException(status_code=404, detail="Material not found in this collection")
    
    material.collection_id = None
    await db.commit()
    
    return {"status": "success"}
