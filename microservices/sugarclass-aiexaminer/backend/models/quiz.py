from sqlalchemy import Column, String, Integer, JSON, DateTime, Text
from backend.database import Base
from datetime import datetime
import uuid

class Collection(Base):
    __tablename__ = "collections"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Material(Base):
    __tablename__ = "materials"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String)
    file_path = Column(String)
    extracted_text = Column(String)
    collection_id = Column(String, index=True, nullable=True)  # Link to collection/folder
    session_id = Column(String, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Quiz(Base):
    __tablename__ = "quizzes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    material_id = Column(String, nullable=True)
    title = Column(String)
    source_text = Column(String)
    questions = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class Progress(Base):
    __tablename__ = "progress"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, index=True)
    quiz_id = Column(String)
    score = Column(Integer)
    total_questions = Column(Integer)
    completed_at = Column(DateTime, default=datetime.utcnow)
