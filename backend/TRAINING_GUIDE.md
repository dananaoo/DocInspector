# Training Guide - Custom YOLO Model

## Overview

This guide will train a custom YOLOv8 model to detect **signatures**, **stamps**, and **QR codes** on construction documents.

## Dataset Structure

```
backend/data/
├── pdfs/                    # Original PDF documents
├── annotations/
│   └── selected_annotations.json  # Ground truth labels
└── yolo_dataset/           # Generated YOLO dataset (after preparation)
    ├── images/
    │   ├── train/
    │   ├── val/
    │   └── test/
    ├── labels/
    │   ├── train/
    │   ├── val/
    │   └── test/
    └── dataset.yaml        # YOLO config file
```

## Step 1: Prepare Dataset

Convert PDFs and annotations to YOLO format:

```bash
cd backend
python prepare_dataset.py
```

**Options:**
```bash
python prepare_dataset.py \
  --annotations data/annotations/selected_annotations.json \
  --pdfs data/pdfs \
  --output data/yolo_dataset \
  --train-split 0.7 \
  --val-split 0.2 \
  --test-split 0.1 \
  --dpi 150
```

**What this does:**
- ✅ Converts each PDF page to an image (JPG)
- ✅ Converts bounding boxes from pixels to YOLO format (normalized)
- ✅ Splits data into train (70%), val (20%), test (10%)
- ✅ Creates `dataset.yaml` configuration file

**Output:**
```
✓ Found X pages with annotations across Y PDFs
📊 Split: N train, M val, K test
✅ Dataset preparation complete!
📊 Annotation statistics:
   - Signatures: XXX
   - Stamps: YYY
   - QR codes: ZZZ
```

## Step 2: Train Model

Train YOLOv8 on your dataset:

```bash
python train_model.py
```

**Quick training (for testing):**
```bash
python train_model.py --epochs 50 --batch 8
```

**Full training (recommended):**
```bash
python train_model.py --model n --epochs 100 --batch 16
```

**Advanced options:**
```bash
python train_model.py \
  --data data/yolo_dataset/dataset.yaml \
  --model s \
  --epochs 150 \
  --imgsz 640 \
  --batch 16 \
  --name digital_inspector_v1
```

### Model Sizes

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| `n` (nano) | Smallest | Fastest | Good | Testing, fast inference |
| `s` (small) | Small | Fast | Better | **Recommended** |
| `m` (medium) | Medium | Medium | Best | High accuracy needed |
| `l` (large) | Large | Slow | Excellent | Max accuracy |
| `x` (xlarge) | Largest | Slowest | Best | Research only |

**Recommendation:** Start with `n` for fast testing, then use `s` or `m` for production.

### Training Parameters

- `--epochs`: Number of training iterations (50-200)
  - More epochs = better accuracy (up to a point)
  - Training stops early if no improvement (patience=20)
- `--batch`: Batch size (8, 16, 32)
  - Larger = faster training, more memory
  - If you get OOM errors, reduce batch size
- `--imgsz`: Image size (640 recommended)
  - Larger = better accuracy, more memory

### Memory Issues?

If you run out of memory:
```bash
python train_model.py --batch 8 --model n
```

Or use CPU (slower):
```bash
python train_model.py --device cpu
```

## Step 3: Monitor Training

During training, you'll see:
```
Epoch   GPU_mem   box_loss   cls_loss   dfl_loss  Instances  Size
1/100     1.2G      1.234      0.567      0.890        123    640
...
```

**What to watch:**
- **Losses should decrease** over time
- **mAP50** should increase (target: > 0.8)
- Training auto-stops if no improvement for 20 epochs

**View results:**
```
runs/train/digital_inspector/
├── weights/
│   ├── best.pt          # 🏆 Best model (use this!)
│   └── last.pt          # Last checkpoint
├── results.png          # Training curves
├── confusion_matrix.png # Performance by class
└── val_batch0_pred.jpg  # Example predictions
```

## Step 4: Use Trained Model

Update your backend to use the trained model:

### Option A: Automatic (in code)

```python
# In detect.py or main.py
detector = DocumentDetector(
    model_path="runs/train/digital_inspector/weights/best.pt"
)
```

### Option B: Copy to backend

```bash
cp runs/train/digital_inspector/weights/best.pt models/digital_inspector_v1.pt
```

Then:
```python
detector = DocumentDetector(model_path="models/digital_inspector_v1.pt")
```

## Step 5: Test Your Model

Test on a new document:

```bash
# Update detect.py to use your model
python test_detection.py test_images/test1.pdf
```

Or via API:
```bash
# Start server
python main.py

# Test
curl -X POST "http://localhost:8000/detect" \
  -F "file=@test_images/test1.pdf"
```

You should now see **signatures**, **stamps**, and **QR codes** detected! 🎉

## Training Tips

### 1. Quick Smoke Test
Before full training, do a quick test:
```bash
python train_model.py --epochs 10 --batch 8
```

### 2. Improve Accuracy
- ✅ Train longer: `--epochs 150`
- ✅ Use larger model: `--model s` or `--model m`
- ✅ Add more training data (if available)
- ✅ Adjust confidence threshold in inference

### 3. Faster Training
- ✅ Use GPU (auto-detected if available)
- ✅ Increase batch size: `--batch 32`
- ✅ Use smaller model: `--model n`

### 4. Expected Performance
With this dataset (~40-50 PDFs), you should get:
- **mAP50**: 0.75-0.90
- **Signatures**: Good detection
- **Stamps**: Good detection
- **QR codes**: Excellent detection

## Troubleshooting

### "CUDA out of memory"
```bash
python train_model.py --batch 8 --model n
```

### "No module named 'ultralytics'"
```bash
pip install ultralytics
```

### Training is too slow
- Use smaller model: `--model n`
- Reduce image size: `--imgsz 480`
- Use GPU if available

### Poor accuracy
- Train longer: `--epochs 150`
- Use more data (if available)
- Try different model: `--model s` or `--model m`

## Next Steps

Once trained:
1. ✅ Copy `best.pt` to a safe location
2. ✅ Update `detect.py` to use your model
3. ✅ Test on real documents
4. ✅ Deploy to production!

## Full Training Command Example

```bash
# Prepare dataset
python prepare_dataset.py

# Train model (recommended settings)
python train_model.py \
  --model s \
  --epochs 100 \
  --batch 16 \
  --name digital_inspector_v1

# Test
python test_detection.py test_images/test1.pdf
```

Good luck with training! 🚀

