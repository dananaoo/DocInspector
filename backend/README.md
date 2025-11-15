# Digital Inspector - Backend API v2

AI-powered detection of **signatures**, **stamps/seals**, and **QR codes** on construction documents using custom-trained YOLOv8.

## 🎯 Features

- ✅ Custom YOLOv8 model (76% mAP50)
- ✅ PDF and image support
- ✅ FastAPI REST API with database
- ✅ **Storage optimized**: 200x less storage (on-demand image generation)
- ✅ Background processing
- ✅ Stable API endpoints

## 📊 Current Model Performance

```
Overall:   76.4% mAP50
QR codes:  99.5% ⭐ Perfect!
Stamps:    85.6% ✅ Excellent
Signatures: 44.1% ⚠️  Good (can improve)
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Start API Server

```bash
# Use the new API v2 (storage optimized)
python api_v2.py
```

Or with uvicorn:

```bash
uvicorn api_v2:app --reload --host 0.0.0.0 --port 8000
```

API runs on: `http://localhost:8000`

### 3. API Documentation

Interactive docs: `http://localhost:8000/docs`

## 📡 Key Endpoints

```
POST   /api/documents/upload        - Upload PDF
GET    /api/documents               - List all documents
GET    /api/documents/{id}          - Get document details
GET    /api/documents/{id}/pages    - Get pages
GET    /api/pages/{id}/detections   - Get detections
GET    /api/pages/{id}/image        - Get annotated image
DELETE /api/documents/{id}          - Delete document
```

## 🧪 Testing

### Quick Test
```bash
# Automated test
./test_api.sh

# Manual test
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@data/pdfs/АПЗ-.pdf"
```

### API Usage Examples

#### Upload Document
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "document_id": 1,
  "filename": "document.pdf",
  "total_pages": 9,
  "status": "processing"
}
```

#### Get Document Pages
```bash
curl "http://localhost:8000/api/documents/1/pages"
```

#### Get Page Detections
```bash
curl "http://localhost:8000/api/pages/1/detections"
```

#### Get Annotated Image (Generated On-Demand)
```bash
curl "http://localhost:8000/api/pages/1/image" -o page_1.jpg
```

### JavaScript Example

```javascript
// Upload PDF
const formData = new FormData();
formData.append('file', pdfFile);

const res = await fetch('http://localhost:8000/api/documents/upload', {
  method: 'POST',
  body: formData
});

const { document_id } = await res.json();

// Get pages
const pagesRes = await fetch(`http://localhost:8000/api/documents/${document_id}/pages`);
const { pages } = await pagesRes.json();

// Display images
pages.forEach(page => {
  const img = `http://localhost:8000/api/pages/${page.page_id}/image`;
  // Use img URL in your frontend
});
```

## 📊 Response Format

### Document Details
```json
{
  "id": 1,
  "filename": "document.pdf",
  "total_pages": 9,
  "status": "completed",
  "summary": {
    "total_detections": 25,
    "by_class": {
      "signature": 8,
      "stamp": 5,
      "qr": 12
    }
  }
}
```

### Page Detections
```json
{
  "page_id": 1,
  "page_number": 1,
  "detections_count": 3,
  "detections": [
    {
      "id": 1,
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
    }
  ]
}
```

## 📁 Project Structure

```
backend/
├── api_v2.py              # FastAPI server (NEW - use this!)
├── database.py            # Database models
├── detect.py              # YOLO detection logic
├── main.py                # Old API (deprecated)
├── prepare_dataset.py     # Dataset preparation
├── train_model.py         # Model training
├── test_all_pages.py      # Test script for PDFs
├── requirements.txt       # Dependencies
├── runs/train/            # Training outputs
│   └── digital_inspector_v1/
│       └── weights/
│           └── best.pt    # Trained model ✅
└── data/
    ├── pdfs/              # Original PDFs
    ├── annotations/       # Ground truth
    └── yolo_dataset/      # Training data
```

## 💾 Storage Design

**Efficient Storage**: Only PDF + JSON stored permanently!

- ❌ **No** permanent image files
- ✅ Images generated on-demand from PDF + detections
- ✅ 200x less storage (5GB vs 100GB for 1000 docs)

See [STORAGE_OPTIMIZATION.md](STORAGE_OPTIMIZATION.md) for details.

## 🔧 Improving Model Accuracy

### Current Performance
- QR codes: 99.5% ⭐ Perfect
- Stamps: 85.6% ✅ Great
- Signatures: 44.1% ⚠️ Needs improvement

### Train Better Model

```bash
# More epochs
python train_model.py --model n --epochs 150 --name v2

# Larger model
python train_model.py --model s --epochs 100 --name v2

# Swap to use new model
cp runs/train/v2/weights/best.pt \
   runs/train/digital_inspector_v1/weights/best.pt

# API automatically uses improved model!
```

## 📚 Documentation

| File | Description |
|------|-------------|
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Complete API reference |
| [STORAGE_OPTIMIZATION.md](STORAGE_OPTIMIZATION.md) | Storage design details |
| [QUICKSTART_V2.md](QUICKSTART_V2.md) | Quick start guide |
| [TRAINING_GUIDE.md](TRAINING_GUIDE.md) | How to train models |
| [NEXT_STEPS.md](NEXT_STEPS.md) | Improvement guide |

