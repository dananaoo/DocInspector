"""
FastAPI Backend for Digital Inspector
API endpoint for document detection using YOLO.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
from pathlib import Path
import tempfile
import os
from typing import List, Dict
import uvicorn

from detect import DocumentDetector

app = FastAPI(
    title="Digital Inspector API",
    description="API for detecting signatures, stamps, and QR codes on construction documents",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize detector (lazy loading)
detector: DocumentDetector = None


def get_detector() -> DocumentDetector:
    """Get or create detector instance."""
    global detector
    if detector is None:
        detector = DocumentDetector()
    return detector


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Digital Inspector API",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/detect": "POST - Upload image for detection",
            "/docs": "API documentation"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Digital Inspector"}


@app.post("/detect")
async def detect_objects(
    file: UploadFile = File(..., description="Image or PDF file to analyze"),
    page: int = 0
):
    """
    Detect signatures, stamps, and QR codes in uploaded document (image or PDF).
    
    Args:
        file: Image or PDF file
        page: Page number for PDFs (0-indexed, default: 0)
    
    Returns:
        - JSON with detection results (bounding boxes, classes, confidence)
    """
    # Validate file type (image or PDF)
    is_pdf = file.filename and file.filename.lower().endswith('.pdf')
    is_image = file.content_type and file.content_type.startswith('image/')
    
    if not (is_pdf or is_image):
        raise HTTPException(
            status_code=400, 
            detail="File must be an image (jpg, png, etc.) or PDF"
        )
    
    # Create temporary files
    suffix = Path(file.filename).suffix if file.filename else ('.pdf' if is_pdf else '.jpg')
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_input:
        # Save uploaded file
        content = await file.read()
        tmp_input.write(content)
        tmp_input_path = tmp_input.name
    
    output_image_path = None
    try:
        # Get detector
        detector = get_detector()
        
        # Run detection
        if is_pdf:
            annotated_image, detections, total_pages = detector.detect_pdf(tmp_input_path, page)
            response_data = {
                "success": True,
                "filename": file.filename,
                "file_type": "pdf",
                "page_processed": page,
                "total_pages": total_pages,
                "detections_count": len(detections),
                "detections": detections,
                "note": "Pretrained YOLOv8 model detects general objects, not signatures/stamps/QR codes. Train a custom model for document-specific detection."
            }
        else:
            annotated_image, detections = detector.detect(tmp_input_path)
            response_data = {
                "success": True,
                "filename": file.filename,
                "file_type": "image",
                "detections_count": len(detections),
                "detections": detections,
                "note": "Pretrained YOLOv8 model detects general objects, not signatures/stamps/QR codes. Train a custom model for document-specific detection."
            }
        
        # Save annotated image to temp file (for potential future use)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_output:
            cv2.imwrite(tmp_output.name, annotated_image)
            output_image_path = tmp_output.name
        
        # Return JSON response
        return JSONResponse(content=response_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")
    
    finally:
        # Cleanup temp files
        if os.path.exists(tmp_input_path):
            os.unlink(tmp_input_path)
        if output_image_path and os.path.exists(output_image_path):
            os.unlink(output_image_path)


@app.post("/detect/with-image")
async def detect_objects_with_image(
    file: UploadFile = File(..., description="Image or PDF file to analyze"),
    page: int = 0
):
    """
    Detect objects and return annotated image.
    
    Args:
        file: Image or PDF file
        page: Page number for PDFs (0-indexed, default: 0)
    
    Returns the annotated image file with bounding boxes drawn.
    """
    # Validate file type (image or PDF)
    is_pdf = file.filename and file.filename.lower().endswith('.pdf')
    is_image = file.content_type and file.content_type.startswith('image/')
    
    if not (is_pdf or is_image):
        raise HTTPException(
            status_code=400, 
            detail="File must be an image (jpg, png, etc.) or PDF"
        )
    
    # Create temporary files
    suffix = Path(file.filename).suffix if file.filename else ('.pdf' if is_pdf else '.jpg')
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_input:
        content = await file.read()
        tmp_input.write(content)
        tmp_input_path = tmp_input.name
    
    try:
        # Get detector
        detector = get_detector()
        
        # Run detection
        if is_pdf:
            annotated_image, detections, total_pages = detector.detect_pdf(tmp_input_path, page)
        else:
            annotated_image, detections = detector.detect(tmp_input_path)
        
        # Save annotated image to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_output:
            cv2.imwrite(tmp_output.name, annotated_image)
            output_image_path = tmp_output.name
        
        # Return image file
        return FileResponse(
            output_image_path,
            media_type="image/jpeg",
            filename="annotated_image.jpg",
            headers={
                "X-Detections-Count": str(len(detections)),
                "X-File-Type": "pdf" if is_pdf else "image"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")
    
    finally:
        # Cleanup input temp file (output will be deleted after response)
        if os.path.exists(tmp_input_path):
            os.unlink(tmp_input_path)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

