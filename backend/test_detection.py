"""
Simple test script for the detection pipeline.
Run this to verify the setup works correctly.
"""

import sys
from pathlib import Path
from detect import DocumentDetector

def test_detection(image_path: str):
    """Test the detection pipeline on an image or PDF."""
    print(f"Testing detection on: {image_path}")
    print("-" * 50)
    
    if not Path(image_path).exists():
        print(f"❌ Error: File not found: {image_path}")
        print("\nUsage: python test_detection.py <path_to_image_or_pdf>")
        return
    
    try:
        # Initialize detector
        print("📦 Loading YOLO model...")
        detector = DocumentDetector()
        print("✓ Model loaded successfully")
        
        # Check if PDF or image
        is_pdf = image_path.lower().endswith('.pdf')
        
        # Run detection
        print(f"\n🔍 Running detection on {image_path}...")
        if is_pdf:
            annotated_image, detections, total_pages = detector.detect_pdf(image_path)
            print(f"  PDF has {total_pages} page(s), processing page 0")
        else:
            annotated_image, detections = detector.detect(image_path)
        
        # Print results
        print(f"\n✓ Detection complete!")
        print(f"  Found {len(detections)} objects:")
        if len(detections) == 0:
            print("    (No objects detected)")
            print("    ⚠️  This is expected with pretrained YOLO model!")
            print("    ⚠️  See NEXT_STEPS.md for how to train a custom model.")
        for i, det in enumerate(detections, 1):
            print(f"    {i}. {det['class']} (confidence: {det['confidence']:.2f})")
            bbox = det['bbox']
            print(f"       Location: ({bbox['x1']}, {bbox['y1']}) to ({bbox['x2']}, {bbox['y2']})")
        
        # Save results
        output_image = "test_output_annotated.jpg"
        output_json = "test_output_results.json"
        detector.save_results(image_path, output_image, output_json)
        
        print(f"\n✅ Test completed successfully!")
        print(f"   Check {output_image} for annotated image")
        print(f"   Check {output_json} for JSON results")
        
    except Exception as e:
        print(f"❌ Error during detection: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_detection.py <path_to_image_or_pdf>")
        print("\nExamples:")
        print("  python test_detection.py test_images/document1.jpg")
        print("  python test_detection.py test_images/document1.pdf")
        sys.exit(1)
    
    test_detection(sys.argv[1])

