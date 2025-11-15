"""
Digital Inspector API v2 - Production Ready
Stable API with database storage.
Frontend won't break when model accuracy improves!
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
import cv2
import shutil
from pathlib import Path
import tempfile
import os
from datetime import datetime

from detect import DocumentDetector
from database import (
    init_db, get_db, 
    create_document, create_page, create_detection,
    get_document, get_all_documents, get_document_pages, get_page_detections,
    update_document_status, delete_document,
    Document, Page, Detection
)

app = FastAPI(
    title="Digital Inspector API v2",
    description="Detect signatures, stamps, and QR codes on construction documents",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Create uploads directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Initialize detector (lazy loading)
detector: DocumentDetector = None


def get_detector() -> DocumentDetector:
    """Get or create detector instance"""
    global detector
    if detector is None:
        detector = DocumentDetector()
    return detector


# Background task for processing
async def process_document_task(document_id: int, file_path: str):
    """
    Background task to process document.
    Only stores PDF + detection JSON (no images saved to disk!)
    """
    from database import SessionLocal
    db = SessionLocal()
    
    try:
        # Update status
        update_document_status(db, document_id, "processing")
        
        # Get detector
        det = get_detector()
        
        # Get total pages
        import fitz
        pdf_doc = fitz.open(file_path)
        total_pages = len(pdf_doc)
        pdf_doc.close()
        
        # Process each page
        for page_num in range(total_pages):
            try:
                # Detect on page (we only need detections, not the image)
                _, detections, _ = det.detect_pdf(file_path, page_num)
                
                # Create page record (no image_path!)
                page = create_page(db, document_id, page_num + 1)
                
                # Create detection records (store JSON data in DB)
                for det_data in detections:
                    create_detection(
                        db,
                        page.id,
                        det_data['class'],
                        det_data['confidence'],
                        det_data['bbox']
                    )
                
                # Update page detection count
                page.detections_count = len(detections)
                page.processed_at = datetime.utcnow()
                db.commit()
                
            except Exception as e:
                print(f"Error processing page {page_num + 1}: {e}")
                continue
        
        # Mark as completed
        update_document_status(db, document_id, "completed")
        
    except Exception as e:
        print(f"Error processing document {document_id}: {e}")
        update_document_status(db, document_id, "failed")
    finally:
        db.close()


# === API ENDPOINTS ===

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Digital Inspector API v2",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "upload": "POST /api/documents/upload",
            "list": "GET /api/documents",
            "document": "GET /api/documents/{id}",
            "pages": "GET /api/documents/{id}/pages",
            "detections": "GET /api/pages/{id}/detections"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Digital Inspector API v2",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/documents/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF document for processing.
    Processing happens in background.
    
    Returns document ID immediately, check status with GET /api/documents/{id}
    """
    # Validate file
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Save file
    file_path = UPLOAD_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Get page count
    import fitz
    pdf_doc = fitz.open(str(file_path))
    total_pages = len(pdf_doc)
    pdf_doc.close()
    
    # Create document record
    doc = create_document(db, file.filename, str(file_path), total_pages)
    
    # Start background processing
    background_tasks.add_task(process_document_task, doc.id, str(file_path))
    
    return {
        "success": True,
        "document_id": doc.id,
        "filename": file.filename,
        "total_pages": total_pages,
        "status": "processing",
        "message": "Document uploaded successfully. Processing in background.",
        "check_status": f"/api/documents/{doc.id}"
    }


@app.get("/api/documents")
async def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all uploaded documents"""
    documents = get_all_documents(db, skip, limit)
    
    return {
        "total": len(documents),
        "documents": [
            {
                "id": doc.id,
                "filename": doc.filename,
                "total_pages": doc.total_pages,
                "status": doc.status,
                "uploaded_at": doc.uploaded_at.isoformat(),
                "processed_at": doc.processed_at.isoformat() if doc.processed_at else None
            }
            for doc in documents
        ]
    }


@app.get("/api/documents/{document_id}")
async def get_document_details(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get document details with summary"""
    doc = get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    pages = get_document_pages(db, document_id)
    
    # Calculate summary
    total_detections = sum(p.detections_count for p in pages)
    class_counts = {}
    for page in pages:
        detections = get_page_detections(db, page.id)
        for det in detections:
            class_counts[det.class_name] = class_counts.get(det.class_name, 0) + 1
    
    return {
        "id": doc.id,
        "filename": doc.filename,
        "total_pages": doc.total_pages,
        "status": doc.status,
        "uploaded_at": doc.uploaded_at.isoformat(),
        "processed_at": doc.processed_at.isoformat() if doc.processed_at else None,
        "summary": {
            "total_detections": total_detections,
            "by_class": class_counts,
            "pages_processed": len([p for p in pages if p.processed_at])
        }
    }


@app.get("/api/documents/{document_id}/pages")
async def get_document_pages_list(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Get all pages for a document"""
    doc = get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    pages = get_document_pages(db, document_id)
    
    return {
        "document_id": document_id,
        "total_pages": len(pages),
        "pages": [
            {
                "page_id": p.id,
                "page_number": p.page_number,
                "detections_count": p.detections_count,
                "processed_at": p.processed_at.isoformat() if p.processed_at else None,
                "image_url": f"/api/pages/{p.id}/image"  # Always available (generated on-demand)
            }
            for p in pages
        ]
    }


@app.get("/api/pages/{page_id}/detections")
async def get_page_detections_list(
    page_id: int,
    db: Session = Depends(get_db)
):
    """Get all detections for a page"""
    from database import get_page
    page = get_page(db, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    detections = get_page_detections(db, page_id)
    
    return {
        "page_id": page_id,
        "page_number": page.page_number,
        "document_id": page.document_id,
        "detections_count": len(detections),
        "detections": [
            {
                "id": det.id,
                "class": det.class_name,
                "confidence": det.confidence,
                "bbox": {
                    "x1": det.bbox_x1,
                    "y1": det.bbox_y1,
                    "x2": det.bbox_x2,
                    "y2": det.bbox_y2,
                    "width": det.bbox_width,
                    "height": det.bbox_height
                }
            }
            for det in detections
        ]
    }


@app.get("/api/pages/{page_id}/image")
async def get_page_image(
    page_id: int,
    db: Session = Depends(get_db)
):
    """
    Get annotated image for a page.
    Generates on-demand from PDF + detection JSON (not stored permanently!)
    """
    from database import get_page
    import tempfile
    import fitz
    
    page = get_page(db, page_id)
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    
    doc = get_document(db, page.document_id)
    if not doc or not Path(doc.file_path).exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    try:
        # Get detections from database
        detections_data = get_page_detections(db, page_id)
        
        # Convert PDF page to image
        pdf_doc = fitz.open(doc.file_path)
        pdf_page = pdf_doc[page.page_number - 1]  # 0-indexed
        
        # Get page dimensions from JSON
        page_rect = pdf_page.rect
        target_width = int(page_rect.width * 2)  # 2x for better quality
        target_height = int(page_rect.height * 2)
        
        zoom_x = target_width / page_rect.width
        zoom_y = target_height / page_rect.height
        mat = fitz.Matrix(zoom_x, zoom_y)
        pix = pdf_page.get_pixmap(matrix=mat)
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        pix.save(temp_file.name)
        pdf_doc.close()
        
        # Load with OpenCV
        image = cv2.imread(temp_file.name)
        
        # Draw detections from database
        for det in detections_data:
            # Scale coordinates if needed
            x1 = int(det.bbox_x1 * zoom_x)
            y1 = int(det.bbox_y1 * zoom_y)
            x2 = int(det.bbox_x2 * zoom_x)
            y2 = int(det.bbox_y2 * zoom_y)
            
            # Get color based on class
            colors = {
                'signature': (0, 255, 0),    # Green
                'stamp': (255, 0, 0),        # Blue
                'qr': (0, 0, 255),           # Red
            }
            color = colors.get(det.class_name, (0, 255, 255))
            
            # Draw bounding box
            cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
            
            # Add label
            label = f"{det.class_name} {det.confidence:.2f}"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(image, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)
            cv2.putText(image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Save final image to temporary file
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
        cv2.imwrite(output_file.name, image)
        
        # Clean up intermediate temp file
        Path(temp_file.name).unlink()
        
        # Return the generated image
        return FileResponse(
            output_file.name,
            media_type="image/jpeg",
            filename=f"page_{page.page_number}.jpg",
            background=None  # Don't delete immediately, let OS handle it
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate image: {str(e)}")


@app.delete("/api/documents/{document_id}")
async def delete_document_endpoint(
    document_id: int,
    db: Session = Depends(get_db)
):
    """Delete a document and all its data"""
    doc = get_document(db, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete PDF file
    if Path(doc.file_path).exists():
        Path(doc.file_path).unlink()
    
    # Delete from database (cascades to pages and detections)
    delete_document(db, document_id)
    
    return {"success": True, "message": "Document deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

