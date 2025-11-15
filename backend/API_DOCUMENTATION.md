# Digital Inspector API v2 Documentation

## 🎯 Key Features

- ✅ **Stable API**: Frontend won't break when you improve the model!
- ✅ **Database Storage**: All results stored in SQLite
- ✅ **Background Processing**: Upload returns immediately
- ✅ **RESTful Design**: Standard HTTP methods
- ✅ **CORS Enabled**: Frontend can call from any domain

## 🚀 Quick Start

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Start Server
```bash
python api_v2.py
```

API will run on: `http://localhost:8000`
Docs: `http://localhost:8000/docs`

## 📡 API Endpoints

### 1. Upload Document
**POST** `/api/documents/upload`

Upload a PDF for processing. Processing happens in background.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "success": true,
  "document_id": 1,
  "filename": "document.pdf",
  "total_pages": 9,
  "status": "processing",
  "message": "Document uploaded successfully. Processing in background.",
  "check_status": "/api/documents/1"
}
```

---

### 2. List All Documents
**GET** `/api/documents`

Get list of all uploaded documents.

**Request:**
```bash
curl "http://localhost:8000/api/documents?skip=0&limit=10"
```

**Response:**
```json
{
  "total": 5,
  "documents": [
    {
      "id": 1,
      "filename": "document.pdf",
      "total_pages": 9,
      "status": "completed",
      "uploaded_at": "2025-11-15T10:30:00",
      "processed_at": "2025-11-15T10:31:00"
    }
  ]
}
```

---

### 3. Get Document Details
**GET** `/api/documents/{document_id}`

Get detailed info about a document with detection summary.

**Request:**
```bash
curl "http://localhost:8000/api/documents/1"
```

**Response:**
```json
{
  "id": 1,
  "filename": "document.pdf",
  "total_pages": 9,
  "status": "completed",
  "uploaded_at": "2025-11-15T10:30:00",
  "processed_at": "2025-11-15T10:31:00",
  "summary": {
    "total_detections": 25,
    "by_class": {
      "signature": 8,
      "stamp": 5,
      "qr": 12
    },
    "pages_processed": 9
  }
}
```

---

### 4. Get Document Pages
**GET** `/api/documents/{document_id}/pages`

Get all pages for a document.

**Request:**
```bash
curl "http://localhost:8000/api/documents/1/pages"
```

**Response:**
```json
{
  "document_id": 1,
  "total_pages": 9,
  "pages": [
    {
      "page_id": 1,
      "page_number": 1,
      "detections_count": 3,
      "processed_at": "2025-11-15T10:30:15",
      "image_url": "/api/pages/1/image"
    },
    {
      "page_id": 2,
      "page_number": 2,
      "detections_count": 5,
      "processed_at": "2025-11-15T10:30:20",
      "image_url": "/api/pages/2/image"
    }
  ]
}
```

---

### 5. Get Page Detections
**GET** `/api/pages/{page_id}/detections`

Get all detections for a specific page.

**Request:**
```bash
curl "http://localhost:8000/api/pages/1/detections"
```

**Response:**
```json
{
  "page_id": 1,
  "page_number": 1,
  "document_id": 1,
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
    },
    {
      "id": 2,
      "class": "qr",
      "confidence": 0.95,
      "bbox": {
        "x1": 500,
        "y1": 600,
        "x2": 600,
        "y2": 700,
        "width": 100,
        "height": 100
      }
    }
  ]
}
```

---

### 6. Get Page Image
**GET** `/api/pages/{page_id}/image`

Get annotated image for a page (with bounding boxes drawn).

**Request:**
```bash
curl "http://localhost:8000/api/pages/1/image" --output page_1.jpg
```

**Response:** JPEG image file

---

### 7. Delete Document
**DELETE** `/api/documents/{document_id}`

Delete a document and all its data.

**Request:**
```bash
curl -X DELETE "http://localhost:8000/api/documents/1"
```

**Response:**
```json
{
  "success": true,
  "message": "Document deleted"
}
```

---

## 🎨 Frontend Integration Example

### JavaScript/React Example

```javascript
// 1. Upload document
async function uploadDocument(file) {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch('http://localhost:8000/api/documents/upload', {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  return data.document_id;
}

// 2. Check status
async function checkStatus(documentId) {
  const response = await fetch(`http://localhost:8000/api/documents/${documentId}`);
  const data = await response.json();
  return data.status; // "processing", "completed", or "failed"
}

// 3. Get results
async function getResults(documentId) {
  const response = await fetch(`http://localhost:8000/api/documents/${documentId}/pages`);
  const data = await response.json();
  return data.pages;
}

// 4. Display detections
async function getDetections(pageId) {
  const response = await fetch(`http://localhost:8000/api/pages/${pageId}/detections`);
  const data = await response.json();
  return data.detections;
}

// Full workflow
async function processDocument(file) {
  // Upload
  const docId = await uploadDocument(file);
  console.log('Uploaded:', docId);
  
  // Poll for completion
  let status = 'processing';
  while (status === 'processing') {
    await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
    status = await checkStatus(docId);
    console.log('Status:', status);
  }
  
  // Get results
  const pages = await getResults(docId);
  console.log('Pages:', pages);
  
  return { docId, pages };
}
```

---

## 🔒 Why This Design?

### Stable Contract
The API structure **never changes**, even when you improve the model:

```
Before (mAP50=0.76):
  /api/pages/1/detections
  → [{ "class": "qr", "confidence": 0.85, "bbox": {...} }]

After (mAP50=0.95):
  /api/pages/1/detections
  → [{ "class": "qr", "confidence": 0.97, "bbox": {...} }]
```

**Same structure**, just better confidence! Frontend doesn't need any changes.

### What You Can Change Without Breaking Frontend

✅ Train new model with more epochs
✅ Use larger model (yolov8s, yolov8m)
✅ Adjust confidence threshold
✅ Add more training data
✅ Fine-tune model parameters

All these improvements **work automatically** - no frontend changes needed!

---

## 🗄️ Database Schema

```
documents
├── id (PK)
├── filename
├── file_path
├── total_pages
├── status
├── uploaded_at
└── processed_at

pages
├── id (PK)
├── document_id (FK)
├── page_number
├── image_path
├── detections_count
└── processed_at

detections
├── id (PK)
├── page_id (FK)
├── class_name
├── confidence
├── bbox_x1, bbox_y1
├── bbox_x2, bbox_y2
└── created_at
```

---

## 🧪 Testing

### Test Upload
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@data/pdfs/АПЗ-.pdf"
```

### Test Status
```bash
curl "http://localhost:8000/api/documents/1"
```

### Test Detections
```bash
curl "http://localhost:8000/api/pages/1/detections"
```

---

## 📊 Response Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid file, etc.) |
| 404 | Not found (document/page doesn't exist) |
| 500 | Server error |

---

## 🔄 Workflow

```
1. Frontend uploads PDF
   ↓
2. API saves to DB (status: "processing")
   ↓
3. Background task processes pages
   ↓
4. Each page → YOLO detection → save to DB
   ↓
5. Status changes to "completed"
   ↓
6. Frontend polls and gets results
```

---

## 💡 Best Practices

1. **Poll for status** after upload (check every 2-5 seconds)
2. **Cache results** on frontend - don't re-fetch unnecessarily
3. **Show progress** - display "X of Y pages processed"
4. **Handle errors** - check for "failed" status
5. **Use pagination** when listing many documents

---

## 🎯 Next Steps for Your Friend (Frontend Developer)

**He can start building now!** The API is stable and ready.

Frontend TODO:
1. Upload page with drag & drop
2. List of processed documents
3. Document viewer with pagination
4. Detections overlay on images
5. Filter by class (signatures/stamps/QR)
6. Export results to CSV/PDF

All while you improve model accuracy in the background! 🚀

