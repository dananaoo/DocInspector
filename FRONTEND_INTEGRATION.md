# Frontend Integration Guide

This document explains how the frontend connects to the backend API.

## ✅ What Was Done

### 1. Created API Client (`frontend/src/api/client.ts`)

A TypeScript client that communicates with the backend:

```typescript
- uploadDocument(file: File) → POST /api/documents/upload
- getDocuments() → GET /api/documents
- getDocument(id) → GET /api/documents/{id}
- getDocumentPages(documentId) → GET /api/documents/{id}/pages
- getPageDetections(pageId) → GET /api/pages/{id}/detections
- getPageImageUrl(pageId) → /api/pages/{id}/image
- deleteDocument(id) → DELETE /api/documents/{id}
- pollDocumentStatus() → Polls until processing complete
```

### 2. Updated Components

#### **App.tsx**
- Replaced mock data with real API calls
- Added document loading on mount (`useEffect`)
- Implemented real upload with polling
- Added real delete functionality
- Integrated toast notifications for user feedback

#### **HomePage.tsx**
- Updated to only accept PDF files
- Real upload triggers API call
- Shows success/error toasts

#### **DocumentsList.tsx**
- Updated to use number IDs (backend uses integers)
- Real-time document list from backend

#### **DocumentView.tsx**
- Fetches pages and detections from backend
- Uses real annotated images from `/api/pages/{id}/image`
- Converts backend bbox format to frontend percentages
- Shows loading state while fetching

### 3. Added Vite Proxy

**`frontend/vite.config.ts`**:
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
  },
}
```

This allows the frontend to call `/api/documents/upload` instead of `http://localhost:8000/api/documents/upload`, avoiding CORS issues.

### 4. Environment Variables

Created `.env.example`:
```bash
VITE_API_URL=  # Leave empty for dev (uses proxy)
```

In production, set to your backend URL.

## 🔄 Data Flow

### Upload Flow

```
1. User drops PDF on HomePage
   ↓
2. Frontend: POST /api/documents/upload
   ↓
3. Backend: Saves PDF, starts background processing
   ↓
4. Backend: Returns { document_id, status: "processing" }
   ↓
5. Frontend: Adds doc to list with "In Queue" status
   ↓
6. Frontend: Polls GET /api/documents/{id} every 2 seconds
   ↓
7. Backend: Processes (YOLO detection on each page)
   ↓
8. Backend: Status changes to "completed"
   ↓
9. Frontend: Updates UI, shows "Processed" status
   ↓
10. User clicks "Open" → Navigate to DocumentView
```

### View Flow

```
1. DocumentView loads
   ↓
2. Frontend: GET /api/documents/{id}/pages
   ↓
3. Backend: Returns list of pages with page_ids
   ↓
4. Frontend: For each page, GET /api/pages/{page_id}/detections
   ↓
5. Backend: Returns detections (bbox, class, confidence)
   ↓
6. Frontend: Renders pages with:
   - Image from /api/pages/{page_id}/image (generated on-demand!)
   - Bounding boxes overlaid on image
   - Detection list in sidebar
```

## 🎯 Key Features Implemented

### ✅ Real-time Processing
- Uploads trigger background processing
- Frontend polls status automatically
- User sees "In Queue" → "Processed" transition

### ✅ On-Demand Image Generation
- Backend doesn't store annotated images
- Generated fresh when requested
- Frontend caches naturally via browser

### ✅ Detection Visualization
- Bounding boxes drawn from backend coordinates
- Different colors for QR, Signature, Stamp
- Click to highlight specific detection
- Toggle boxes, labels, confidence on/off

### ✅ Multi-Page Support
- Sidebar thumbnails for navigation
- Lazy loading of detection data
- Smooth page switching

### ✅ Error Handling
- Toast notifications for errors
- Loading states during API calls
- Graceful failure handling

## 🧪 Testing the Integration

### 1. Start Backend

```bash
cd backend
python api_v2.py
```

Should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Start Frontend

```bash
cd frontend
npm install  # First time only
npm run dev
```

Should open browser at `http://localhost:3000`

### 3. Test Upload

1. Drop a PDF on the upload area
2. Should see toast: "Document uploaded successfully!"
3. Status should show "In Queue"
4. After a few seconds: "Document processing completed!"
5. Status changes to "Processed"

### 4. Test View

1. Click "Open" on a processed document
2. Should load page thumbnails on left
3. Main view shows annotated image
4. Right sidebar shows detections by type
5. Click a detection → image scrolls to it

### 5. Test Delete

1. Go to Documents list
2. Hover over a document
3. Click trash icon
4. Document disappears from list

## 🐛 Troubleshooting

### Frontend can't connect to backend

**Check:**
1. Backend is running: `curl http://localhost:8000/api/documents`
2. Vite proxy is configured (check `vite.config.ts`)
3. No firewall blocking localhost:8000

### Images not loading

**Check:**
1. Document status is "completed"
2. Backend generated images: `curl http://localhost:8000/api/pages/1/image -o test.jpg`
3. Browser console for 404 errors

### Bounding boxes in wrong place

**Issue:** Backend bbox coordinates might not match image dimensions.

**Fix:** Update `DocumentView.tsx` bbox conversion logic:
```typescript
bbox: {
  x: (det.bbox_x1 / IMAGE_WIDTH) * 100,
  y: (det.bbox_y1 / IMAGE_HEIGHT) * 100,
  width: ((det.bbox_x2 - det.bbox_x1) / IMAGE_WIDTH) * 100,
  height: ((det.bbox_y2 - det.bbox_y1) / IMAGE_HEIGHT) * 100
}
```

You'll need to get actual image dimensions from backend or metadata.

## 📝 API Contract

The frontend expects these backend responses:

### Upload Response
```json
{
  "document_id": 1,
  "filename": "document.pdf",
  "total_pages": 9,
  "status": "processing"
}
```

### Document Response
```json
{
  "id": 1,
  "filename": "document.pdf",
  "upload_date": "2025-11-15",
  "total_pages": 9,
  "status": "completed",
  "summary": {
    "total_detections": 25,
    "by_class": {
      "qr": 12,
      "signature": 8,
      "stamp": 5
    }
  }
}
```

### Pages Response
```json
{
  "pages": [
    {
      "page_id": 1,
      "page_number": 1,
      "document_id": 1,
      "detections_count": 3
    }
  ]
}
```

### Detections Response
```json
{
  "page_id": 1,
  "page_number": 1,
  "detections_count": 3,
  "detections": [
    {
      "id": 1,
      "class_name": "qr",
      "confidence": 0.95,
      "bbox_x1": 100,
      "bbox_y1": 200,
      "bbox_x2": 150,
      "bbox_y2": 250
    }
  ]
}
```

## ✨ Result

**The frontend is now fully connected to your backend!**

- No backend changes needed ✅
- Uses your trained YOLO model ✅
- Real document upload & processing ✅
- Real detection visualization ✅
- Storage-optimized (on-demand images) ✅

Your friend can now work on improving the UI while you enhance the model accuracy - both work independently! 🎉

