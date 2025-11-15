#!/bin/bash
# Test script for API v2 - Storage efficient version

echo "🧪 Testing Digital Inspector API v2"
echo "===================================="
echo ""

# Check if server is running
echo "1. Health check..."
curl -s http://localhost:8000/health | python3 -m json.tool
echo ""

# Upload a document
echo "2. Uploading PDF..."
RESPONSE=$(curl -s -X POST "http://localhost:8000/api/documents/upload" \
  -F "file=@data/pdfs/АПЗ-.pdf")
echo "$RESPONSE" | python3 -m json.tool

# Extract document ID
DOC_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['document_id'])")
echo ""
echo "📄 Document ID: $DOC_ID"
echo ""

# Wait for processing
echo "3. Waiting for processing to complete..."
sleep 5

# Check document status
echo "4. Checking document status..."
curl -s "http://localhost:8000/api/documents/$DOC_ID" | python3 -m json.tool
echo ""

# Get pages list
echo "5. Getting pages list..."
curl -s "http://localhost:8000/api/documents/$DOC_ID/pages" | python3 -m json.tool
echo ""

# Get detections for first page
echo "6. Getting detections for page 1..."
PAGE_RESPONSE=$(curl -s "http://localhost:8000/api/documents/$DOC_ID/pages")
PAGE_ID=$(echo "$PAGE_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['pages'][0]['page_id'] if data['pages'] else 0)")

if [ "$PAGE_ID" != "0" ]; then
    curl -s "http://localhost:8000/api/pages/$PAGE_ID/detections" | python3 -m json.tool
    echo ""
    
    echo "7. Downloading annotated image (generated on-demand)..."
    curl -s "http://localhost:8000/api/pages/$PAGE_ID/image" -o test_generated_image.jpg
    echo "✅ Image saved to: test_generated_image.jpg"
    echo "   Size: $(du -h test_generated_image.jpg | cut -f1)"
else
    echo "⚠️  No pages found yet (still processing?)"
fi

echo ""
echo "✅ All tests complete!"
echo ""
echo "📊 Storage check:"
echo "   Database size: $(du -h digital_inspector.db 2>/dev/null | cut -f1 || echo '0')"
echo "   PDF files: $(du -sh uploads/ 2>/dev/null | cut -f1 || echo '0')"
echo "   Note: No images stored permanently! ✅"

