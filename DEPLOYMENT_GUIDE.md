# 🚀 Deployment Guide - Digital Inspector

## Current Status

✅ **Model Trained**: mAP50 = 0.764 (76.4%)
✅ **API Ready**: Stable v2 endpoints with database
✅ **Detection Working**: 80-90% accuracy
✅ **Ready for Production**: Frontend can start now!

## 📋 What We Have

### 1. Trained Model
- **Location**: `backend/runs/train/digital_inspector_v1/weights/best.pt`
- **Performance**: 
  - QR codes: 99.5% mAP50 (excellent!)
  - Stamps: 85.6% mAP50 (very good)
  - Signatures: 44.1% mAP50 (good, can improve)
- **Auto-loaded**: API automatically uses this model

### 2. API Endpoints
- **File**: `backend/api_v2.py`
- **Database**: SQLite (`digital_inspector.db`)
- **Docs**: `backend/API_DOCUMENTATION.md`

### 3. Key Features
- Upload PDF → Background processing
- Store results in database
- RESTful API (GET, POST, DELETE)
- CORS enabled for frontend

---

## 🎯 For Frontend Developer

### Quick Start

1. **Start API**:
   ```bash
   cd backend
   python api_v2.py
   ```
   API runs on: `http://localhost:8000`

2. **View Docs**:
   Open: `http://localhost:8000/docs`

3. **Test Upload**:
   ```bash
   curl -X POST "http://localhost:8000/api/documents/upload" \
     -F "file=@data/pdfs/АПЗ-.pdf"
   ```

### API Endpoints You'll Use

```
POST   /api/documents/upload        - Upload PDF
GET    /api/documents               - List documents
GET    /api/documents/{id}          - Get document details
GET    /api/documents/{id}/pages    - Get all pages
GET    /api/pages/{id}/detections   - Get detections
GET    /api/pages/{id}/image        - Get annotated image
DELETE /api/documents/{id}          - Delete document
```

### Example Frontend Flow

```javascript
// 1. Upload
const formData = new FormData();
formData.append('file', pdfFile);
const res = await fetch('http://localhost:8000/api/documents/upload', {
  method: 'POST',
  body: formData
});
const { document_id } = await res.json();

// 2. Poll for completion
let status = 'processing';
while (status === 'processing') {
  await sleep(2000);
  const res = await fetch(`http://localhost:8000/api/documents/${document_id}`);
  const doc = await res.json();
  status = doc.status;
}

// 3. Get results
const res = await fetch(`http://localhost:8000/api/documents/${document_id}/pages`);
const { pages } = await res.json();

// 4. Display each page
for (const page of pages) {
  const img = `http://localhost:8000/api/pages/${page.page_id}/image`;
  const detectionsRes = await fetch(`http://localhost:8000/api/pages/${page.page_id}/detections`);
  const { detections } = await detectionsRes.json();
  
  // Now display image with detections overlay
}
```

---

## 🔧 For Backend Developer (You)

### Improving Model Without Breaking Frontend

**The key**: API stays the same, model improves behind the scenes!

#### Option 1: Train with More Epochs

```bash
cd backend
python train_model.py --model n --epochs 100 --name digital_inspector_v2
```

Then copy new model:
```bash
cp runs/train/digital_inspector_v2/weights/best.pt \
   runs/train/digital_inspector_v1/weights/best.pt
```

API automatically uses improved model! 🎉

#### Option 2: Use Larger Model

```bash
# Small model (better accuracy)
python train_model.py --model s --epochs 100

# Medium model (best balance)
python train_model.py --model m --epochs 100
```

#### Option 3: Add More Training Data

1. Add more PDFs to `data/pdfs/`
2. Update `data/annotations/selected_annotations.json`
3. Regenerate dataset:
   ```bash
   python prepare_dataset.py
   ```
4. Retrain:
   ```bash
   python train_model.py --model n --epochs 100
   ```

#### Option 4: Adjust Confidence Threshold

Edit `backend/detect.py`:
```python
# Line 142 - lower = more detections, higher = fewer false positives
if confidence < 0.25:  # Change this value
    continue
```

---

## 📊 Current Model Performance

```
Overall:
  mAP50:       76.4%
  Precision:   84.8%
  Recall:      77.3%

By Class:
  QR codes:    99.5% mAP50 ⭐ Perfect!
  Stamps:      85.6% mAP50 ✅ Excellent
  Signatures:  44.1% mAP50 ⚠️  Needs improvement
```

### How to Improve Signatures

1. **Train longer**:
   ```bash
   python train_model.py --epochs 150
   ```

2. **Use larger model**:
   ```bash
   python train_model.py --model s --epochs 100
   ```

3. **Check training data**:
   - Are signature annotations accurate?
   - Do you have enough signature examples?

4. **Adjust augmentation** in `train_model.py`:
   ```python
   model.train(
       ...
       fliplr=0.5,  # Horizontal flip
       mosaic=1.0,  # Mosaic augmentation
   )
   ```

---

## 🗄️ Database

**File**: `digital_inspector.db` (auto-created)

**Schema**:
- `documents` - Uploaded PDFs
- `pages` - Individual pages
- `detections` - Detected objects

**View data**:
```bash
sqlite3 digital_inspector.db
> SELECT * FROM documents;
> SELECT * FROM detections;
```

**Reset database**:
```bash
rm digital_inspector.db
# Will be recreated on next run
```

---

## 🚀 Deployment Options

### Option 1: Local Development
```bash
python api_v2.py
```

### Option 2: Production Server
```bash
gunicorn api_v2:app --workers 4 --bind 0.0.0.0:8000
```

### Option 3: Docker (Future)
Create `Dockerfile`:
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "api_v2.py"]
```

---

## 📝 Testing Checklist

Before giving to frontend:

- [ ] API starts without errors
- [ ] Can upload PDF
- [ ] Processing completes
- [ ] Can view detections
- [ ] Can get annotated images
- [ ] Database stores results correctly

Test commands:
```bash
# Upload
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@data/pdfs/АПЗ-.pdf"

# Check (use ID from above)
curl "http://localhost:8000/api/documents/1"

# Get pages
curl "http://localhost:8000/api/documents/1/pages"

# Get detections
curl "http://localhost:8000/api/pages/1/detections"
```

---

## 🎯 Roadmap

### Phase 1: Current ✅
- [x] Base detection pipeline
- [x] Trained model (76% mAP50)
- [x] API v2 with database
- [x] Background processing

### Phase 2: Accuracy Improvements
- [ ] Improve signature detection (target: >70%)
- [ ] Train with more epochs (100+)
- [ ] Try larger model (yolov8s/m)
- [ ] Add more training data

### Phase 3: Features
- [ ] Multi-document batch upload
- [ ] PDF export with annotations
- [ ] User authentication
- [ ] Cloud storage (S3)

---

## 🆘 Troubleshooting

### "Model not found"
```bash
# Check model exists
ls backend/runs/train/digital_inspector_v1/weights/best.pt

# If not, retrain
cd backend
python train_model.py --epochs 20
```

### "Database locked"
```bash
# Close all connections and restart
pkill -f api_v2
python api_v2.py
```

### "Port already in use"
```bash
# Kill existing process
lsof -ti:8000 | xargs kill -9
python api_v2.py
```

---

## 📞 Contact

**Backend Developer**: Works on model accuracy
**Frontend Developer**: Builds UI using stable API

The API contract won't change - work independently! 🚀

