"""
Database models and operations for Digital Inspector.
Stores documents, pages, and detections.
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./digital_inspector.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Models
class Document(Base):
    """Document table - stores uploaded PDFs"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    file_path = Column(String)
    total_pages = Column(Integer)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    
    # Relationships
    pages = relationship("Page", back_populates="document", cascade="all, delete-orphan")


class Page(Base):
    """Page table - stores individual PDF pages metadata only"""
    __tablename__ = "pages"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), index=True)
    page_number = Column(Integer)  # 1-indexed
    processed_at = Column(DateTime, nullable=True)
    detections_count = Column(Integer, default=0)
    
    # Note: No image_path! Images generated on-demand from PDF + detections JSON
    
    # Relationships
    document = relationship("Document", back_populates="pages")
    detections = relationship("Detection", back_populates="page", cascade="all, delete-orphan")


class Detection(Base):
    """Detection table - stores individual detected objects"""
    __tablename__ = "detections"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"), index=True)
    class_name = Column(String, index=True)  # signature, stamp, qr
    confidence = Column(Float)
    bbox_x1 = Column(Integer)
    bbox_y1 = Column(Integer)
    bbox_x2 = Column(Integer)
    bbox_y2 = Column(Integer)
    bbox_width = Column(Integer)
    bbox_height = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    page = relationship("Page", back_populates="detections")


# Database utilities
def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session (for FastAPI dependency injection)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_document(db, filename: str, file_path: str, total_pages: int):
    """Create a new document record"""
    doc = Document(
        filename=filename,
        file_path=file_path,
        total_pages=total_pages,
        status="pending"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def create_page(db, document_id: int, page_number: int):
    """Create a new page record"""
    page = Page(
        document_id=document_id,
        page_number=page_number
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return page


def create_detection(db, page_id: int, class_name: str, confidence: float, bbox: dict):
    """Create a new detection record"""
    detection = Detection(
        page_id=page_id,
        class_name=class_name,
        confidence=confidence,
        bbox_x1=bbox['x1'],
        bbox_y1=bbox['y1'],
        bbox_x2=bbox['x2'],
        bbox_y2=bbox['y2'],
        bbox_width=bbox.get('width', bbox['x2'] - bbox['x1']),
        bbox_height=bbox.get('height', bbox['y2'] - bbox['y1'])
    )
    db.add(detection)
    db.commit()
    db.refresh(detection)
    return detection


def get_document(db, document_id: int):
    """Get document by ID"""
    return db.query(Document).filter(Document.id == document_id).first()


def get_all_documents(db, skip: int = 0, limit: int = 100):
    """Get all documents with pagination"""
    return db.query(Document).offset(skip).limit(limit).all()


def get_page(db, page_id: int):
    """Get page by ID"""
    return db.query(Page).filter(Page.id == page_id).first()


def get_document_pages(db, document_id: int):
    """Get all pages for a document"""
    return db.query(Page).filter(Page.document_id == document_id).order_by(Page.page_number).all()


def get_page_detections(db, page_id: int):
    """Get all detections for a page"""
    return db.query(Detection).filter(Detection.page_id == page_id).all()


def update_document_status(db, document_id: int, status: str):
    """Update document processing status"""
    doc = get_document(db, document_id)
    if doc:
        doc.status = status
        if status == "completed":
            doc.processed_at = datetime.utcnow()
        db.commit()
        db.refresh(doc)
    return doc


def delete_document(db, document_id: int):
    """Delete document and all related data"""
    doc = get_document(db, document_id)
    if doc:
        db.delete(doc)
        db.commit()
    return True

