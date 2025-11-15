"""
Train YOLOv8 model on the Digital Inspector dataset.
"""

from ultralytics import YOLO
from pathlib import Path
import argparse


def train_yolo_model(
    dataset_yaml: str,
    model_size: str = 'n',
    epochs: int = 100,
    imgsz: int = 640,
    batch: int = 16,
    project: str = 'runs/train',
    name: str = 'digital_inspector',
    pretrained: bool = True,
    device: str = None
):
    """
    Train YOLO model on construction document dataset.
    
    Args:
        dataset_yaml: Path to dataset.yaml file
        model_size: Model size (n, s, m, l, x). 'n' is fastest, 'x' is most accurate
        epochs: Number of training epochs
        imgsz: Image size for training
        batch: Batch size (reduce if running out of memory)
        project: Project directory for saving runs
        name: Name for this training run
        pretrained: Whether to start from pretrained COCO weights
        device: Device to train on (None for auto-detect, 'cpu', '0', '0,1', etc.)
    """
    print("=" * 60)
    print("🚀 Digital Inspector - YOLO Training")
    print("=" * 60)
    
    # Check if dataset exists
    dataset_path = Path(dataset_yaml)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_yaml}")
    
    print(f"\n📊 Dataset: {dataset_path.absolute()}")
    print(f"🤖 Model: YOLOv8{model_size}")
    print(f"📈 Epochs: {epochs}")
    print(f"📐 Image size: {imgsz}")
    print(f"📦 Batch size: {batch}")
    
    # Initialize model
    model_name = f'yolov8{model_size}.pt' if pretrained else f'yolov8{model_size}.yaml'
    print(f"\n🔧 Loading model: {model_name}")
    model = YOLO(model_name)
    
    # Train
    print(f"\n🏃 Starting training...")
    print("-" * 60)
    
    results = model.train(
        data=str(dataset_path),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        project=project,
        name=name,
        device=device,
        # Training hyperparameters
        patience=20,  # Early stopping patience
        save=True,
        save_period=10,  # Save checkpoint every 10 epochs
        cache=False,  # Cache images for faster training (use if you have RAM)
        # Augmentation
        flipud=0.0,  # No vertical flip for documents
        fliplr=0.5,  # Horizontal flip is ok
        mosaic=1.0,  # Mosaic augmentation
        mixup=0.0,  # No mixup for documents
        # Optimizer
        optimizer='auto',
        lr0=0.01,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        # Loss
        box=7.5,
        cls=0.5,
        dfl=1.5,
        # Other
        verbose=True,
        plots=True
    )
    
    print("\n" + "=" * 60)
    print("✅ Training complete!")
    print("=" * 60)
    
    # Print results
    best_model_path = Path(project) / name / 'weights' / 'best.pt'
    last_model_path = Path(project) / name / 'weights' / 'last.pt'
    
    print(f"\n📁 Results saved to: {Path(project) / name}")
    print(f"\n🏆 Best model: {best_model_path}")
    print(f"📊 Last model: {last_model_path}")
    
    # Validation
    print(f"\n🧪 Running validation on best model...")
    model = YOLO(str(best_model_path))
    metrics = model.val(data=str(dataset_path))
    
    print(f"\n📊 Validation Metrics:")
    print(f"   - mAP50: {metrics.box.map50:.4f}")
    print(f"   - mAP50-95: {metrics.box.map:.4f}")
    print(f"   - Precision: {metrics.box.mp:.4f}")
    print(f"   - Recall: {metrics.box.mr:.4f}")
    
    print(f"\n💡 To use this model in your app:")
    print(f"   detector = DocumentDetector(model_path='{best_model_path}')")
    
    return best_model_path


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Train YOLO model on Digital Inspector dataset')
    
    parser.add_argument('--data', type=str,
                       default='data/yolo_dataset/dataset.yaml',
                       help='Path to dataset.yaml')
    parser.add_argument('--model', type=str, default='n',
                       choices=['n', 's', 'm', 'l', 'x'],
                       help='Model size (n=nano, s=small, m=medium, l=large, x=xlarge)')
    parser.add_argument('--epochs', type=int, default=100,
                       help='Number of epochs (default: 100)')
    parser.add_argument('--imgsz', type=int, default=640,
                       help='Image size (default: 640)')
    parser.add_argument('--batch', type=int, default=16,
                       help='Batch size (default: 16, reduce if OOM)')
    parser.add_argument('--project', type=str, default='runs/train',
                       help='Project directory')
    parser.add_argument('--name', type=str, default='digital_inspector',
                       help='Run name')
    parser.add_argument('--no-pretrained', action='store_true',
                       help='Train from scratch (no pretrained weights)')
    parser.add_argument('--device', type=str, default=None,
                       help='Device (None=auto, cpu, 0, 0,1, etc.)')
    
    args = parser.parse_args()
    
    train_yolo_model(
        dataset_yaml=args.data,
        model_size=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=args.project,
        name=args.name,
        pretrained=not args.no_pretrained,
        device=args.device
    )


if __name__ == '__main__':
    main()

