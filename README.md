# Digital Inspector
Demo: https://youtu.be/gFEfWWid7yI

🤖 AI-powered detection of **signatures**, **stamps/seals**, and **QR codes** on construction documents using custom-trained YOLOv8.

## 🎯 Features

- ✅ Custom YOLOv8 model trained on construction documents
- ✅ PDF and image support
- ✅ FastAPI REST API
- ✅ Detects: signatures, stamps, QR codes
- ✅ Returns annotated images + JSON coordinates
- ✅ 258 annotations across 91 document pages

## 📊 Project Status

- **Dataset**: ✅ Prepared (91 pages, 258 annotations)
- **Training**: 🏃 In Progress (YOLOv8n, 100 epochs)
- **Backend**: ✅ Ready
- **API**: ✅ Deployed

## 🚀 Quick Start

### Option 1: Full Stack (Backend + Frontend)

```bash
# Terminal 1: Start Backend
cd backend
pip install -r requirements.txt
python api_v2.py

# Terminal 2: Start Frontend
cd frontend
npm install
npm run dev
```

Open browser: `http://localhost:3000`

### Option 2: Backend Only (API Testing)

```bash
cd backend
pip install -r requirements.txt
python api_v2.py
```

API: `http://localhost:8000/docs`

Test upload:
```bash
curl -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@backend/data/pdfs/АПЗ-.pdf"
```

## 📁 Project Structure

```
armeta/
├── backend/
│   ├── api_v2.py               # FastAPI server ⭐
│   ├── detect.py               # YOLO detection logic
│   ├── database.py             # Database models
│   ├── prepare_dataset.py      # Dataset preparation
│   ├── train_model.py          # Model training
│   ├── requirements.txt        # Python dependencies
│   ├── data/
│   │   ├── pdfs/               # Original documents
│   │   ├── annotations/        # Ground truth labels
│   │   └── yolo_dataset/       # Prepared YOLO dataset
│   └── runs/train/             # Training outputs
│       └── digital_inspector_v1/
│           └── weights/
│               └── best.pt     # 🏆 Trained model (76% mAP50)
├── frontend/                   # React UI ⭐
│   ├── src/
│   │   ├── api/client.ts       # Backend API client
│   │   ├── components/         # UI components
│   │   ├── App.tsx             # Main app
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts          # Vite config with proxy
│   └── README.md
├── TRAINING_SUMMARY.md         # Training results
├── FRONTEND_INTEGRATION.md     # Integration guide ⭐
└── README.md                   # This file
```

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [backend/README.md](backend/README.md) | Backend setup and API guide |
| [frontend/README.md](frontend/README.md) | Frontend setup guide ⭐ |
| [FRONTEND_INTEGRATION.md](FRONTEND_INTEGRATION.md) | How frontend connects to backend ⭐ |
| [backend/API_DOCUMENTATION.md](backend/API_DOCUMENTATION.md) | Complete API reference |
| [backend/TRAINING_GUIDE.md](backend/TRAINING_GUIDE.md) | How to train YOLO models |
| [TRAINING_SUMMARY.md](TRAINING_SUMMARY.md) | Model performance results |
| [backend/STORAGE_OPTIMIZATION.md](backend/STORAGE_OPTIMIZATION.md) | Storage design details |

## 🎓 Training Your Own Model

### Prepare Dataset
```bash
cd backend
python prepare_dataset.py \
  --annotations data/annotations/selected_annotations.json \
  --pdfs data/pdfs \
  --output data/yolo_dataset
```

### Train Model
```bash
python train_model.py --model n --epochs 100 --name my_model
```

### Use Trained Model
The detector automatically finds and uses your trained model:
```python
from detect import DocumentDetector
detector = DocumentDetector()  # Auto-loads best.pt
```

See [TRAINING_SUMMARY.md](TRAINING_SUMMARY.md) for details.

## 🧪 API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Detect Objects (JSON)
```bash
curl -X POST "http://localhost:8000/detect?page=0" \
  -F "file=@document.pdf"
```

### Get Annotated Image
```bash
curl -X POST "http://localhost:8000/detect/with-image?page=0" \
  -F "file=@document.pdf" \
  --output annotated.jpg
```

## 📊 Dataset Statistics

- **Total Documents**: 45 PDFs
- **Pages with Annotations**: 91
- **Total Annotations**: 258
  - Signatures: 103
  - Stamps: 60
  - QR Codes: 95
- **Train/Val/Test**: 63 / 18 / 10 pages

## 🔧 Tech Stack

- **Python 3.8+**
- **YOLOv8** (ultralytics)
- **FastAPI** - REST API
- **PyMuPDF** - PDF processing
- **OpenCV** - Image processing
- **PyTorch** - Deep learning

## 📈 Performance

Expected metrics (after training):
- **mAP50**: 0.75-0.90
- **Precision**: 0.80-0.95
- **Recall**: 0.75-0.90

## 🎯 Use Cases

- ✅ Construction document verification
- ✅ Automated signature detection
- ✅ Stamp/seal validation
- ✅ QR code scanning
- ✅ Document processing pipelines

## 🐛 Troubleshooting

### No detections found
- Training might not be complete yet
- Check `runs/train/digital_inspector_v1/weights/best.pt` exists
- See [backend/NEXT_STEPS.md](backend/NEXT_STEPS.md)

### Out of memory during training
```bash
python train_model.py --batch 8 --model n
```

### Model not found
```bash
# Check training output
ls runs/train/*/weights/

# Or specify path manually
detector = DocumentDetector(model_path="path/to/best.pt")
```

## 🚀 Deployment

1. Train model: `python train_model.py`
2. Test locally: `python test_detection.py test.pdf`
3. Deploy API: `python main.py`
4. Use in production!

## 📝 License

MIT

## 👥 Contributing

This is a custom solution for construction document analysis. For questions or improvements, please open an issue.

---

**Status**: 🏃 Training in progress (check TRAINING_SUMMARY.md for updates)

