# Digital Inspector - Backend

Document analysis tool that automatically detects signatures, stamps/seals, and QR codes on construction documents using YOLOv8.

## Features

- 🎯 YOLOv8-based object detection
- 📄 Detects: signatures, stamps/seals, QR codes (requires custom trained model)
- 📄 **PDF Support**: Automatically converts PDF pages to images
- 📦 FastAPI REST API
- 🖼️ Returns annotated images with bounding boxes
- 📊 JSON output with detection coordinates

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run the API Server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### 3. API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Usage

### Command Line (Direct Detection)

Test the detector directly on an image:

```bash
python detect.py path/to/image.jpg output_annotated.jpg output_results.json
```

### API Endpoints

#### 1. Health Check
```bash
curl http://localhost:8000/health
```

#### 2. Detect Objects (JSON response)
```bash
# For images
curl -X POST "http://localhost:8000/detect" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/document.jpg"

# For PDFs (specify page number)
curl -X POST "http://localhost:8000/detect?page=0" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/document.pdf"
```

#### 3. Detect Objects (Get annotated image)
```bash
# For images
curl -X POST "http://localhost:8000/detect/with-image" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/document.jpg" \
  --output annotated_image.jpg

# For PDFs
curl -X POST "http://localhost:8000/detect/with-image?page=0" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/document.pdf" \
  --output annotated_image.jpg
```

### Python Client Example

```python
import requests

# Upload image for detection
with open("document.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/detect",
        files={"file": f}
    )

results = response.json()
print(f"Found {results['detections_count']} objects")
for detection in results['detections']:
    print(f"  - {detection['class']}: {detection['confidence']:.2f}")
```

## Response Format

### JSON Response Example

```json
{
  "success": true,
  "filename": "document.jpg",
  "detections_count": 3,
  "detections": [
    {
      "class": "signature",
      "confidence": 0.85,
      "bbox": {
        "x1": 100,
        "y1": 200,
        "x2": 300,
        "y2": 250,
        "width": 200,
        "height": 50
      }
    },
    {
      "class": "stamp",
      "confidence": 0.92,
      "bbox": {
        "x1": 400,
        "y1": 500,
        "x2": 550,
        "y2": 600,
        "width": 150,
        "height": 100
      }
    }
  ]
}
```

## Project Structure

```
backend/
├── main.py          # FastAPI application
├── detect.py        # YOLO detection logic
├── requirements.txt # Dependencies
└── README.md        # This file
```

## Notes

- **Version 1 (Current)**: Uses pretrained YOLOv8 model (yolov8n.pt). 
  - ⚠️ **Important**: The pretrained model detects general objects (people, cars, etc.), not specifically signatures/stamps/QR codes.
  - The pipeline is ready and will work once you train a custom YOLO model on your document dataset.
  - To use a custom model: `detector = DocumentDetector(model_path="path/to/your/model.pt")`
- **Version 2 (Future)**: Will add OpenCV fallback for signature/stamp detection using template matching or feature detection.

## Testing the Pipeline

Even without a custom trained model, you can test the pipeline:

```bash
# Test with any image (will detect general objects)
python test_detection.py path/to/any/image.jpg

# Or use the direct detection script
python detect.py path/to/image.jpg output.jpg results.json
```

The pipeline structure is complete - you just need to train a YOLO model on your document dataset to detect signatures, stamps, and QR codes specifically.

**📖 See [NEXT_STEPS.md](NEXT_STEPS.md) for detailed guide on why you're getting 0 detections and how to train a custom model.**

## Testing

1. Place test images in a folder (e.g., `test_images/`)
2. Run detection:
   ```bash
   python detect.py test_images/document1.jpg output.jpg results.json
   ```
3. Check the output image and JSON file

## Development

- The detector uses YOLOv8n (nano) by default for speed
- Confidence threshold is set to 0.25 (adjustable in `detect.py`)
- Custom trained models can be loaded by passing `model_path` to `DocumentDetector`

