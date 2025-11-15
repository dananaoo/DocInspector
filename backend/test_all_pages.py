"""
Test detection on ALL pages of a PDF document.
Processes each page separately and saves results.
"""

import sys
import json
from pathlib import Path
from detect import DocumentDetector
import cv2


def test_all_pages(pdf_path: str, output_dir: str = "output"):
    """
    Test detection on all pages of a PDF.
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save outputs (default: "output")
    """
    if not Path(pdf_path).exists():
        print(f"❌ Error: PDF file not found: {pdf_path}")
        return
    
    if not pdf_path.lower().endswith('.pdf'):
        print(f"❌ Error: File must be a PDF")
        return
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print(f"📄 Processing PDF: {pdf_path}")
    print("=" * 60)
    
    # Initialize detector
    print("📦 Loading YOLO model...")
    detector = DocumentDetector()
    
    # Process all pages
    try:
        # First, get total pages
        import fitz
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        doc.close()
        
        print(f"✓ Found {total_pages} pages in PDF\n")
        
        all_results = []
        total_detections = 0
        
        for page_num in range(total_pages):
            print(f"🔍 Processing page {page_num + 1}/{total_pages}...")
            
            try:
                # Detect on this page
                annotated_image, detections, _ = detector.detect_pdf(pdf_path, page_num)
                
                # Save annotated image
                output_image = output_path / f"page_{page_num + 1}_annotated.jpg"
                cv2.imwrite(str(output_image), annotated_image)
                
                # Collect results
                page_result = {
                    'page': page_num + 1,
                    'detections_count': len(detections),
                    'detections': detections,
                    'output_image': str(output_image)
                }
                all_results.append(page_result)
                total_detections += len(detections)
                
                if len(detections) > 0:
                    print(f"  ✓ Found {len(detections)} object(s):")
                    for det in detections:
                        print(f"     - {det['class']}: {det['confidence']:.2f}")
                else:
                    print(f"  - No objects detected")
                
            except Exception as e:
                print(f"  ⚠️  Error processing page {page_num + 1}: {e}")
                continue
        
        # Save combined JSON results
        combined_results = {
            'pdf_path': pdf_path,
            'total_pages': total_pages,
            'total_detections': total_detections,
            'pages': all_results
        }
        
        json_output = output_path / "all_pages_results.json"
        with open(json_output, 'w', encoding='utf-8') as f:
            json.dump(combined_results, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 60)
        print(f"✅ Processing complete!")
        print(f"   Total pages processed: {total_pages}")
        print(f"   Total detections: {total_detections}")
        print(f"   Output directory: {output_path.absolute()}")
        print(f"   Images saved: page_1_annotated.jpg to page_{total_pages}_annotated.jpg")
        print(f"   JSON results: {json_output}")
        
        # Summary by class
        class_counts = {}
        for page in all_results:
            for det in page['detections']:
                class_name = det['class']
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        if class_counts:
            print(f"\n📊 Detection summary:")
            for class_name, count in sorted(class_counts.items()):
                print(f"   - {class_name}: {count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_all_pages.py <pdf_path> [output_dir]")
        print("\nExamples:")
        print("  python test_all_pages.py data/pdfs/АПЗ-.pdf")
        print("  python test_all_pages.py data/pdfs/письмо-.pdf output_results")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output"
    
    test_all_pages(pdf_path, output_dir)

