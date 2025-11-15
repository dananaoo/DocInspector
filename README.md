# Digital Inspector

Automated detection of signatures, stamps/seals, and QR codes on construction documents.

## Project Overview

Digital Inspector is a document analysis tool that uses YOLOv8 to automatically detect and locate:
- ✍️ **Signatures**
- 🔴 **Stamps / Seals**
- 📱 **QR Codes**

## Quick Start

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python main.py
```

API will be available at `http://localhost:8000`

See [backend/README.md](backend/README.md) for detailed documentation.

## Project Structure

```
armeta/
├── backend/
│   ├── main.py          # FastAPI application
│   ├── detect.py        # YOLO detection module
│   ├── requirements.txt # Python dependencies
│   └── README.md        # Backend documentation
├── .cursorrules         # Project rules and guidelines
└── README.md           # This file
```

## Version History

### v1.0 (Current) - Base MVP
- ✅ YOLOv8 detection pipeline
- ✅ FastAPI backend
- ✅ JSON output with coordinates
- ✅ Annotated image output
- ✅ Basic detection on pretrained model

### v2.0 (Planned)
- 🔄 OpenCV fallback for signatures/stamps
- 🔄 Custom trained YOLO model
- 🔄 Improved accuracy

## License

MIT

