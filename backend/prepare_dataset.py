"""
Prepare YOLO dataset from PDF documents and JSON annotations.
Converts PDFs to images and annotations to YOLO format.
"""

import json
import fitz  # PyMuPDF
from pathlib import Path
import shutil
from typing import Dict, List, Tuple
import random

# Class mapping
CLASS_MAP = {
    'signature': 0,
    'stamp': 1,
    'qr': 2
}

def convert_bbox_to_yolo(bbox: Dict, page_width: int, page_height: int) -> Tuple[float, float, float, float]:
    """
    Convert bbox from (x, y, width, height) in pixels to YOLO format.
    YOLO format: (center_x, center_y, width, height) normalized to 0-1.
    
    Args:
        bbox: Dict with x, y, width, height in pixels
        page_width: Page width in pixels
        page_height: Page height in pixels
        
    Returns:
        Tuple of (center_x, center_y, width, height) normalized
    """
    x = bbox['x']
    y = bbox['y']
    w = bbox['width']
    h = bbox['height']
    
    # Calculate center
    center_x = (x + w / 2) / page_width
    center_y = (y + h / 2) / page_height
    
    # Normalize width and height
    norm_width = w / page_width
    norm_height = h / page_height
    
    # Clamp values to [0, 1]
    center_x = max(0, min(1, center_x))
    center_y = max(0, min(1, center_y))
    norm_width = max(0, min(1, norm_width))
    norm_height = max(0, min(1, norm_height))
    
    return center_x, center_y, norm_width, norm_height


def pdf_page_to_image(pdf_path: str, page_num: int, output_path: str, target_width: int, target_height: int):
    """
    Convert a PDF page to an image at EXACT target dimensions.
    
    Args:
        pdf_path: Path to PDF file
        page_num: Page number (0-indexed)
        output_path: Output image path
        target_width: Target width in pixels (from JSON page_size)
        target_height: Target height in pixels (from JSON page_size)
    
    Returns:
        Tuple of (actual_width, actual_height) after rendering
    """
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    
    # Get PDF page dimensions in points
    pdf_rect = page.rect
    pdf_width = pdf_rect.width
    pdf_height = pdf_rect.height
    
    # Calculate scale factors to match target size EXACTLY
    zoom_x = target_width / pdf_width
    zoom_y = target_height / pdf_height
    
    # Create transformation matrix for exact size
    mat = fitz.Matrix(zoom_x, zoom_y)
    pix = page.get_pixmap(matrix=mat)
    pix.save(output_path)
    
    doc.close()
    
    return pix.width, pix.height


def prepare_yolo_dataset(
    annotations_path: str,
    pdfs_dir: str,
    output_dir: str,
    train_split: float = 0.7,
    val_split: float = 0.2,
    test_split: float = 0.1
):
    """
    Prepare YOLO dataset from PDFs and annotations.
    
    CRITICAL: Renders PDFs at EXACT size specified in JSON page_size to ensure
    bounding boxes align correctly!
    
    Args:
        annotations_path: Path to selected_annotations.json
        pdfs_dir: Directory containing PDF files
        output_dir: Output directory for YOLO dataset
        train_split: Fraction for training set
        val_split: Fraction for validation set
        test_split: Fraction for test set
    """
    # Load annotations
    print(f"📖 Loading annotations from {annotations_path}...")
    with open(annotations_path, 'r', encoding='utf-8') as f:
        annotations = json.load(f)
    
    # Create output directories
    output_path = Path(output_dir)
    for split in ['train', 'val', 'test']:
        (output_path / 'images' / split).mkdir(parents=True, exist_ok=True)
        (output_path / 'labels' / split).mkdir(parents=True, exist_ok=True)
    
    # Collect all pages with annotations
    all_pages = []
    for pdf_name, pages in annotations.items():
        for page_name, page_data in pages.items():
            if 'annotations' in page_data and len(page_data['annotations']) > 0:
                all_pages.append((pdf_name, page_name, page_data))
    
    print(f"✓ Found {len(all_pages)} pages with annotations across {len(annotations)} PDFs")
    
    # Shuffle and split
    random.seed(42)
    random.shuffle(all_pages)
    
    n_train = int(len(all_pages) * train_split)
    n_val = int(len(all_pages) * val_split)
    
    train_pages = all_pages[:n_train]
    val_pages = all_pages[n_train:n_train + n_val]
    test_pages = all_pages[n_train + n_val:]
    
    print(f"📊 Split: {len(train_pages)} train, {len(val_pages)} val, {len(test_pages)} test")
    
    # Process each split
    splits = {
        'train': train_pages,
        'val': val_pages,
        'test': test_pages
    }
    
    stats = {'signature': 0, 'stamp': 0, 'qr': 0}
    
    for split_name, pages in splits.items():
        print(f"\n🔄 Processing {split_name} set ({len(pages)} pages)...")
        
        for idx, (pdf_name, page_name, page_data) in enumerate(pages):
            # Extract page number from page_name (e.g., "page_1" -> 0)
            page_num = int(page_name.split('_')[1]) - 1
            
            # Generate output filename
            safe_pdf_name = pdf_name.replace('.pdf', '').replace(' ', '_')
            output_name = f"{safe_pdf_name}_{page_name}"
            
            # Convert PDF page to image
            pdf_path = Path(pdfs_dir) / pdf_name
            if not pdf_path.exists():
                print(f"  ⚠️  Warning: PDF not found: {pdf_path}")
                continue
            
            image_path = output_path / 'images' / split_name / f"{output_name}.jpg"
            
            # Get target size from JSON (THIS IS CRITICAL!)
            json_page_size = page_data.get('page_size', {})
            target_width = int(json_page_size.get('width', 1684))
            target_height = int(json_page_size.get('height', 1190))
            
            try:
                img_width, img_height = pdf_page_to_image(
                    str(pdf_path),
                    page_num,
                    str(image_path),
                    target_width=target_width,
                    target_height=target_height
                )
                
                # Verify size matches (with small tolerance for rounding)
                if abs(img_width - target_width) > 2 or abs(img_height - target_height) > 2:
                    print(f"  ⚠️  Warning: Size mismatch for {output_name}")
                    print(f"     Expected: {target_width}x{target_height}, Got: {img_width}x{img_height}")
            except Exception as e:
                print(f"  ⚠️  Error converting {pdf_name} page {page_num}: {e}")
                continue
            
            # Create YOLO label file
            label_path = output_path / 'labels' / split_name / f"{output_name}.txt"
            
            with open(label_path, 'w') as label_file:
                for annotation in page_data['annotations']:
                    # Get annotation data (structure varies)
                    ann_data = list(annotation.values())[0]
                    category = ann_data['category']
                    bbox = ann_data['bbox']
                    
                    # Get class ID
                    if category not in CLASS_MAP:
                        print(f"  ⚠️  Unknown category: {category}")
                        continue
                    
                    class_id = CLASS_MAP[category]
                    stats[category] = stats.get(category, 0) + 1
                    
                    # Convert bbox to YOLO format
                    # Use the actual image dimensions from conversion
                    center_x, center_y, width, height = convert_bbox_to_yolo(
                        bbox, img_width, img_height
                    )
                    
                    # Write to label file
                    label_file.write(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")
            
            if (idx + 1) % 10 == 0:
                print(f"  Processed {idx + 1}/{len(pages)} pages...")
    
    # Create dataset.yaml
    yaml_content = f"""# Digital Inspector Dataset
path: {output_path.absolute()}
train: images/train
val: images/val
test: images/test

# Classes
names:
  0: signature
  1: stamp
  2: qr

# Dataset info
nc: 3  # number of classes
"""
    
    yaml_path = output_path / 'dataset.yaml'
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)
    
    print(f"\n✅ Dataset preparation complete!")
    print(f"   Output directory: {output_path.absolute()}")
    print(f"   Dataset config: {yaml_path}")
    print(f"\n📊 Annotation statistics:")
    print(f"   - Signatures: {stats['signature']}")
    print(f"   - Stamps: {stats['stamp']}")
    print(f"   - QR codes: {stats['qr']}")
    print(f"   - Total: {sum(stats.values())}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Prepare YOLO dataset from PDFs and annotations')
    parser.add_argument('--annotations', type=str, 
                       default='data/annotations/selected_annotations.json',
                       help='Path to annotations JSON file')
    parser.add_argument('--pdfs', type=str,
                       default='data/pdfs',
                       help='Directory containing PDF files')
    parser.add_argument('--output', type=str,
                       default='data/yolo_dataset',
                       help='Output directory for YOLO dataset')
    parser.add_argument('--train-split', type=float, default=0.7,
                       help='Training set fraction (default: 0.7)')
    parser.add_argument('--val-split', type=float, default=0.2,
                       help='Validation set fraction (default: 0.2)')
    parser.add_argument('--test-split', type=float, default=0.1,
                       help='Test set fraction (default: 0.1)')
    
    args = parser.parse_args()
    
    prepare_yolo_dataset(
        annotations_path=args.annotations,
        pdfs_dir=args.pdfs,
        output_dir=args.output,
        train_split=args.train_split,
        val_split=args.val_split,
        test_split=args.test_split
    )


if __name__ == '__main__':
    main()

