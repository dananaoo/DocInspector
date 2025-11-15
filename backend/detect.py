"""
YOLO Detection Module for Digital Inspector
Detects signatures, stamps/seals, and QR codes on construction documents.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
from ultralytics import YOLO
import json
import tempfile
import os

try:
    import fitz  # PyMuPDF
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


def pdf_to_images(pdf_path: str, dpi: int = 200) -> List[str]:
    """
    Convert PDF pages to images.
    
    Args:
        pdf_path: Path to PDF file
        dpi: Resolution for image conversion (default: 200)
        
    Returns:
        List of temporary image file paths (one per page)
    """
    if not PDF_SUPPORT:
        raise ImportError("PyMuPDF (pymupdf) is required for PDF support. Install with: pip install pymupdf")
    
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    image_paths = []
    
    try:
        for page_num in range(len(doc)):
            page = doc[page_num]
            # Convert page to image (pixmap)
            mat = fitz.Matrix(dpi / 72, dpi / 72)  # 72 is default DPI
            pix = page.get_pixmap(matrix=mat)
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            pix.save(temp_file.name)
            image_paths.append(temp_file.name)
            temp_file.close()
    finally:
        doc.close()
    
    return image_paths


class DocumentDetector:
    """YOLO-based detector for document elements."""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize the detector with a YOLO model.
        
        Args:
            model_path: Path to custom YOLO model. If None, auto-detects trained model or uses pretrained.
            
        Note:
            The pretrained YOLOv8 model detects general objects (people, cars, etc.),
            NOT signatures/stamps/QR codes. You need to train a custom model for
            document-specific detection. See README for details.
        """
        if model_path and Path(model_path).exists():
            self.model = YOLO(model_path)
            print(f"✓ Loaded custom model: {model_path}")
        else:
            # Try to find trained model automatically
            trained_model_paths = [
                'runs/train/digital_inspector_v1/weights/best.pt',
                'runs/train/digital_inspector/weights/best.pt',
                'models/digital_inspector.pt',
                'models/best.pt'
            ]
            
            trained_model = None
            for path in trained_model_paths:
                if Path(path).exists():
                    trained_model = path
                    break
            
            if trained_model:
                self.model = YOLO(trained_model)
                print(f"✓ Loaded trained model: {trained_model}")
            else:
                # Use pretrained YOLOv8 model (will download on first use)
                # WARNING: This model detects general objects, not signatures/stamps/QR codes!
                # For actual document detection, you need a custom trained model.
                self.model = YOLO('yolov8n.pt')  # nano version for speed
                print(f"⚠️  Using pretrained YOLOv8 (not trained for documents)")
        
        # Class names for our use case
        # Note: Using pretrained model, we'll filter for relevant detections
        # In production with custom model, these would be: ['signature', 'stamp', 'qr_code']
        self.target_classes = ['signature', 'stamp', 'seal', 'qr_code', 'qr']
    
    def detect(self, image_path: str, page_num: Optional[int] = None) -> Tuple[np.ndarray, List[Dict]]:
        """
        Run detection on an image.
        
        Args:
            image_path: Path to input image (not PDF - use detect_pdf for PDFs)
            page_num: Not used for images (kept for API compatibility)
            
        Returns:
            Tuple of (annotated_image, detections_list)
            detections_list contains dicts with: class, confidence, bbox (x1, y1, x2, y2)
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image from {image_path}")
        
        # Run YOLO detection
        results = self.model(image)
        
        # Parse results
        detections = []
        annotated_image = image.copy()
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # Get box coordinates (xyxy format)
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                confidence = float(box.conf[0].cpu().numpy())
                class_id = int(box.cls[0].cpu().numpy())
                class_name = self.model.names[class_id]
                
                # Filter by confidence threshold
                if confidence < 0.25:  # Adjust threshold as needed
                    continue
                
                # Store detection
                detection = {
                    'class': class_name,
                    'confidence': round(confidence, 4),
                    'bbox': {
                        'x1': int(x1),
                        'y1': int(y1),
                        'x2': int(x2),
                        'y2': int(y2),
                        'width': int(x2 - x1),
                        'height': int(y2 - y1)
                    }
                }
                detections.append(detection)
                
                # Draw bounding box
                color = self._get_color_for_class(class_name)
                cv2.rectangle(annotated_image, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                
                # Add label
                label = f"{class_name} {confidence:.2f}"
                label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                cv2.rectangle(
                    annotated_image,
                    (int(x1), int(y1) - label_size[1] - 10),
                    (int(x1) + label_size[0], int(y1)),
                    color,
                    -1
                )
                cv2.putText(
                    annotated_image,
                    label,
                    (int(x1), int(y1) - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1
                )
        
        return annotated_image, detections
    
    def _get_color_for_class(self, class_name: str) -> Tuple[int, int, int]:
        """Get color for bounding box based on class."""
        colors = {
            'signature': (0, 255, 0),      # Green
            'stamp': (255, 0, 0),          # Blue
            'seal': (255, 0, 0),           # Blue
            'qr_code': (0, 0, 255),        # Red
            'qr': (0, 0, 255),             # Red
        }
        # Default to yellow for unknown classes
        return colors.get(class_name.lower(), (0, 255, 255))
    
    def detect_pdf(self, pdf_path: str, page_num: Optional[int] = None) -> Tuple[np.ndarray, List[Dict], int]:
        """
        Detect objects in a PDF file.
        
        Args:
            pdf_path: Path to PDF file
            page_num: Page number to process (0-indexed, None = first page)
            
        Returns:
            Tuple of (annotated_image, detections_list, total_pages)
        """
        if not PDF_SUPPORT:
            raise ImportError("PyMuPDF is required for PDF support. Install with: pip install pymupdf")
        
        image_paths = pdf_to_images(pdf_path)
        total_pages = len(image_paths)
        
        if page_num is None:
            page_num = 0
        
        if page_num >= total_pages:
            raise ValueError(f"Page {page_num} not found. PDF has {total_pages} pages.")
        
        try:
            annotated_image, detections = self.detect(image_paths[page_num])
            return annotated_image, detections, total_pages
        finally:
            # Clean up temporary image files
            for img_path in image_paths:
                if os.path.exists(img_path):
                    os.unlink(img_path)
    
    def save_results(self, image_path: str, output_image_path: str, output_json_path: str, page_num: Optional[int] = None):
        """
        Detect and save results to image and JSON file.
        
        Args:
            image_path: Input image or PDF path
            output_image_path: Path to save annotated image
            output_json_path: Path to save JSON results
            page_num: For PDFs, which page to process (None = first page)
        """
        is_pdf = image_path.lower().endswith('.pdf')
        
        if is_pdf:
            annotated_image, detections, total_pages = self.detect_pdf(image_path, page_num)
            results_dict = {
                'file_path': image_path,
                'file_type': 'pdf',
                'page_processed': page_num if page_num is not None else 0,
                'total_pages': total_pages,
                'detections_count': len(detections),
                'detections': detections
            }
        else:
            annotated_image, detections = self.detect(image_path, page_num)
            results_dict = {
                'file_path': image_path,
                'file_type': 'image',
                'detections_count': len(detections),
                'detections': detections
            }
        
        # Save annotated image
        cv2.imwrite(output_image_path, annotated_image)
        
        # Save JSON
        with open(output_json_path, 'w') as f:
            json.dump(results_dict, f, indent=2)
        
        print(f"✓ Saved annotated image to: {output_image_path}")
        print(f"✓ Saved JSON results to: {output_json_path}")
        print(f"✓ Found {len(detections)} detections")
        
        if len(detections) == 0:
            print(f"\n⚠️  NOTE: Pretrained YOLOv8 model doesn't detect signatures/stamps/QR codes.")
            print(f"   You need to train a custom model for document-specific detection.")
            print(f"   See NEXT_STEPS.md for detailed instructions.")
        
        return results_dict


def main():
    """Test the detector on a sample image or PDF."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python detect.py <image_or_pdf_path> [output_image_path] [output_json_path] [page_num]")
        print("\nExamples:")
        print("  python detect.py document.jpg output.jpg results.json")
        print("  python detect.py document.pdf output.jpg results.json 0")
        sys.exit(1)
    
    image_path = sys.argv[1]
    output_image = sys.argv[2] if len(sys.argv) > 2 else "output_annotated.jpg"
    output_json = sys.argv[3] if len(sys.argv) > 3 else "output_results.json"
    page_num = int(sys.argv[4]) if len(sys.argv) > 4 else None
    
    detector = DocumentDetector()
    detector.save_results(image_path, output_image, output_json, page_num)


if __name__ == "__main__":
    main()

