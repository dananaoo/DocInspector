"""
Continue training from an existing model checkpoint.
This is SAFE - creates a new model, doesn't overwrite existing ones.
"""
from ultralytics import YOLO
from pathlib import Path
import argparse


def continue_training(
    checkpoint_path: str,
    dataset_yaml: str,
    epochs: int = 20,
    batch: int = 8,
    project: str = 'runs/train',
    name: str = None,
    device: str = None
):
    """
    Continue training from an existing model checkpoint.
    
    Args:
        checkpoint_path: Path to existing model (best.pt or last.pt)
        dataset_yaml: Path to dataset.yaml file
        epochs: Additional epochs to train
        batch: Batch size
        project: Project directory
        name: Name for this training run (auto-generated if None)
        device: Device to train on
    """
    print("=" * 60)
    print("🔄 Continue Training from Checkpoint")
    print("=" * 60)
    
    # Check checkpoint exists
    checkpoint = Path(checkpoint_path)
    if not checkpoint.exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")
    
    # Check dataset exists
    dataset_path = Path(dataset_yaml)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_yaml}")
    
    # Auto-generate name if not provided
    if name is None:
        # Extract base name from checkpoint path
        base_name = checkpoint.parent.parent.name  # e.g., "digital_inspector_v2"
        name = f"{base_name}_continued"
    
    print(f"\n📊 Dataset: {dataset_path.absolute()}")
    print(f"📦 Checkpoint: {checkpoint.absolute()}")
    print(f"📈 Additional epochs: {epochs}")
    print(f"📐 Image size: (from checkpoint)")
    print(f"📦 Batch size: {batch}")
    print(f"📁 Output name: {name}")
    
    # Load model from checkpoint
    print(f"\n🔧 Loading model from checkpoint: {checkpoint}")
    model = YOLO(str(checkpoint))
    
    # Continue training
    print(f"\n🏃 Continuing training...")
    print("-" * 60)
    
    results = model.train(
        data=str(dataset_path),
        epochs=epochs,
        batch=batch,
        project=project,
        name=name,
        device=device,
        # Training hyperparameters (same as original)
        patience=20,
        save=True,
        save_period=10,
        cache=False,
        # Augmentation
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.0,
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
        plots=True,
        resume=False  # Start fresh training run, not resume (safer)
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
    
    print(f"\n💡 To use this model:")
    print(f"   detector = DocumentDetector(model_path='{best_model_path}')")
    print(f"\n   Or update detect.py to check for '{name}' first!")
    
    return best_model_path


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Continue training YOLO model from checkpoint'
    )
    
    parser.add_argument(
        '--checkpoint',
        type=str,
        required=True,
        help='Path to checkpoint model (e.g., runs/train/digital_inspector_v2/weights/best.pt)'
    )
    parser.add_argument(
        '--data',
        type=str,
        default='data/yolo_dataset/dataset.yaml',
        help='Path to dataset.yaml'
    )
    parser.add_argument(
        '--epochs',
        type=int,
        default=20,
        help='Additional epochs to train (default: 20, optimal based on v2 results)'
    )
    parser.add_argument(
        '--batch',
        type=int,
        default=8,
        help='Batch size (default: 8)'
    )
    parser.add_argument(
        '--project',
        type=str,
        default='runs/train',
        help='Project directory'
    )
    parser.add_argument(
        '--name',
        type=str,
        default=None,
        help='Run name (auto-generated if not provided)'
    )
    parser.add_argument(
        '--device',
        type=str,
        default=None,
        help='Device (None=auto, cpu, 0, 0,1, etc.)'
    )
    
    args = parser.parse_args()
    
    continue_training(
        checkpoint_path=args.checkpoint,
        dataset_yaml=args.data,
        epochs=args.epochs,
        batch=args.batch,
        project=args.project,
        name=args.name,
        device=args.device
    )


if __name__ == '__main__':
    main()

