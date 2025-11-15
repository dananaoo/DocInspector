# Testing Guide

## Quick Test Commands

### Test with PDF
```bash
cd backend
python test_detection.py test_images/test1.pdf
```

### Test with Image
```bash
python test_detection.py path/to/your/image.jpg
```

### Test with CLI detect.py
```bash
# For images
python detect.py image.jpg output.jpg results.json

# For PDFs (page 0)
python detect.py document.pdf output.jpg results.json 0
```

## Test API Server

### 1. Start the server
```bash
python main.py
# or
uvicorn main:app --reload
```

### 2. Test with curl

**Upload PDF:**
```bash
curl -X POST "http://localhost:8000/detect?page=0" \
  -F "file=@test_images/test1.pdf"
```

**Get annotated image from PDF:**
```bash
curl -X POST "http://localhost:8000/detect/with-image?page=0" \
  -F "file=@test_images/test1.pdf" \
  --output annotated.jpg
```

### 3. Test with Python
```python
import requests

# Test detection
with open("test_images/test1.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/detect",
        files={"file": f},
        params={"page": 0}
    )
    print(response.json())
```

## Expected Results

With the **pretrained YOLO model** (current setup), you'll get:
- ✅ **0 detections** for document images/PDFs (expected!)
- ✅ Pipeline works correctly
- ✅ PDF is converted to image
- ✅ Annotated image is saved
- ✅ JSON results are generated

The model detects general objects (people, cars, etc.), not signatures/stamps/QR codes.

## Next Steps

See [NEXT_STEPS.md](NEXT_STEPS.md) for:
- Why you're getting 0 detections
- How to train a custom model
- Dataset preparation guide
- Training instructions

Once you have a trained model:
```python
detector = DocumentDetector(model_path="path/to/your/trained_model.pt")
```

