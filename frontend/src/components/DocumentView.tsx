import { useState, useRef, useEffect } from 'react';
import { ZoomIn, ZoomOut, Download, ArrowLeft, QrCode, PenLine, Stamp } from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Switch } from './ui/switch';
import { Label } from './ui/label';
import type { Document } from '../App';
import { ImageWithFallback } from './figma/ImageWithFallback';
import * as api from '../api/client';

interface DocumentViewProps {
  document: Document;
  onBack: () => void;
}

interface Detection {
  id: string;
  type: 'QR-code' | 'Signature' | 'Stamp';
  confidence: number;
  bbox: { x: number; y: number; width: number; height: number };
  pageNumber: number;
}

interface PageData {
  pageNumber: number;
  pageId: number;
  imageUrl: string;
  detections: Detection[];
}

type DetectionTab = 'QR-code' | 'Signature' | 'Stamp';

// Convert backend class names to frontend types
function convertClassName(className: string): 'QR-code' | 'Signature' | 'Stamp' {
  if (className === 'qr') return 'QR-code';
  if (className === 'signature') return 'Signature';
  return 'Stamp';
}

export function DocumentView({ document, onBack }: DocumentViewProps) {
  const [selectedPage, setSelectedPage] = useState(0);
  const [zoom, setZoom] = useState(100);
  const [showBoxes, setShowBoxes] = useState(true);
  const [showLabels, setShowLabels] = useState(true);
  const [showConfidence, setShowConfidence] = useState(false);
  const [selectedDetection, setSelectedDetection] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<DetectionTab>('QR-code');
  const [pages, setPages] = useState<PageData[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Ref for the document view container to enable scrolling
  const documentContainerRef = useRef<HTMLDivElement>(null);

  // Helper function to get image dimensions
  async function getImageDimensions(imageUrl: string): Promise<{ width: number; height: number }> {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => {
        resolve({ width: img.naturalWidth, height: img.naturalHeight });
      };
      img.onerror = reject;
      img.src = imageUrl;
    });
  }

  // Fetch pages and detections from backend
  useEffect(() => {
    async function loadPagesAndDetections() {
      try {
        setLoading(true);
        
        // Get all pages for this document
        const pagesResponse = await api.getDocumentPages(document.id);
        
        // Fetch detections for each page
        const pagesWithDetections = await Promise.all(
          pagesResponse.pages.map(async (page) => {
            const imageUrl = api.getPageImageUrl(page.page_id);
            const detectionsResponse = await api.getPageDetections(page.page_id);
            
            // Get image dimensions to convert pixel coordinates to percentages
            let imageWidth = 1;
            let imageHeight = 1;
            try {
              const dimensions = await getImageDimensions(imageUrl);
              imageWidth = dimensions.width;
              imageHeight = dimensions.height;
            } catch (error) {
              console.warn(`Failed to get image dimensions for page ${page.page_id}:`, error);
            }
            
            // IMPORTANT: Coordinate conversion
            // The backend stores coordinates at detection size (200 DPI)
            // The backend generates display images at 2x PDF size
            // 
            // Detection: PDF_size * (200/72) = PDF_size * 2.777...
            // Display: PDF_size * 2
            // Scale needed: 2 / 2.777... = 0.72
            //
            // However, the backend also scales coordinates by 2.0 when drawing on the image.
            // So the coordinates in the database are at 200 DPI, but the image is at 2x PDF.
            // We need to scale from 200 DPI to 2x PDF size.
            
            const DETECTION_DPI = 200;
            const DISPLAY_MULTIPLIER = 2.0;
            const POINTS_PER_INCH = 72;
            // Scale from detection size to display size
            // Try different scale factors - start with calculated value
            let SCALE_FACTOR = (DISPLAY_MULTIPLIER * POINTS_PER_INCH) / DETECTION_DPI; // = 0.72
            
            // Alternative: Try matching backend's behavior (it scales by 2.0, but that might be wrong)
            // Or try no scaling if coordinates are already correct
            // SCALE_FACTOR = 1.0; // Uncomment to test without scaling
            // SCALE_FACTOR = 0.72; // Calculated value
            // SCALE_FACTOR = 0.65; // Try slightly different if 0.72 is off
            
            // Debug: Log first detection to help troubleshoot
            if (detectionsResponse.detections.length > 0) {
              const firstDet = detectionsResponse.detections[0];
              console.log(`[Page ${page.page_id}] Image: ${imageWidth}x${imageHeight}, First detection:`, {
                original: { x1: firstDet.bbox.x1, y1: firstDet.bbox.y1, x2: firstDet.bbox.x2, y2: firstDet.bbox.y2 },
                scaleFactor: SCALE_FACTOR,
                scaled: {
                  x1: firstDet.bbox.x1 * SCALE_FACTOR,
                  y1: firstDet.bbox.y1 * SCALE_FACTOR,
                  x2: firstDet.bbox.x2 * SCALE_FACTOR,
                  y2: firstDet.bbox.y2 * SCALE_FACTOR
                }
              });
            }
            
            // Convert backend detections to frontend format
            const detections: Detection[] = detectionsResponse.detections.map((det) => {
              // Scale coordinates from detection size (200 DPI) to display size (2x PDF)
              const scaledX1 = det.bbox.x1 * SCALE_FACTOR;
              const scaledY1 = det.bbox.y1 * SCALE_FACTOR;
              const scaledX2 = det.bbox.x2 * SCALE_FACTOR;
              const scaledY2 = det.bbox.y2 * SCALE_FACTOR;
              
              // Convert to percentages
              const xPercent = (scaledX1 / imageWidth) * 100;
              const yPercent = (scaledY1 / imageHeight) * 100;
              const widthPercent = ((scaledX2 - scaledX1) / imageWidth) * 100;
              const heightPercent = ((scaledY2 - scaledY1) / imageHeight) * 100;
              
              return {
                id: `${page.page_id}-${det.id}`,
                type: convertClassName(det.class),
                confidence: det.confidence,
                pageNumber: page.page_number,
                bbox: {
                  x: xPercent,
                  y: yPercent,
                  width: widthPercent,
                  height: heightPercent
                }
              };
            });
            
            return {
              pageNumber: page.page_number,
              pageId: page.page_id,
              imageUrl,
              detections
            };
          })
        );
        
        setPages(pagesWithDetections);
      } catch (error) {
        console.error('Failed to load pages:', error);
      } finally {
        setLoading(false);
      }
    }
    
    loadPagesAndDetections();
  }, [document.id]);

  // Auto-scroll to detection when selected (must be before early return)
  useEffect(() => {
    if (selectedDetection && documentContainerRef.current && pages.length > 0) {
      const currentPage = pages[selectedPage];
      if (!currentPage) return;
      
      // Find the detection in the current page
      const detection = currentPage.detections.find(d => d.id === selectedDetection);
      if (detection) {
        // Get the container element
        const container = documentContainerRef.current;
        const containerHeight = container.clientHeight;
        
        // Calculate the scroll position based on detection's Y position (as percentage)
        // We want to center the detection in the view
        const targetScrollPercentage = detection.bbox.y / 100;
        const maxScroll = container.scrollHeight - containerHeight;
        const targetScroll = maxScroll * targetScrollPercentage;
        
        // Smooth scroll to the detection
        container.scrollTo({
          top: targetScroll - containerHeight * 0.3, // Offset by 30% from top for better visibility
          behavior: 'smooth'
        });
      }
    }
  }, [selectedDetection, selectedPage, pages]);

  // Show loading state
  if (loading || pages.length === 0) {
    return (
      <div className="max-w-[1800px] mx-auto px-6 py-8">
        <Button
          variant="ghost"
          onClick={onBack}
          className="mb-4 text-[#6B7280] hover:text-[#1A1A1A] -ml-2"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Documents
        </Button>
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-[#4A6CF7] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-[#6B7280]">Loading document...</p>
          </div>
        </div>
      </div>
    );
  }

  const currentPage = pages[selectedPage];
  
  // Get all detections across all pages
  const allDetections = pages.flatMap(page => page.detections);
  const allQrCodes = allDetections.filter(d => d.type === 'QR-code');
  const allSignatures = allDetections.filter(d => d.type === 'Signature');
  const allStamps = allDetections.filter(d => d.type === 'Stamp');

  const getTypeColor = (type: Detection['type']) => {
    switch (type) {
      case 'QR-code':
        return { border: '#9C27B0', bg: 'rgba(156, 39, 176, 0.15)', text: '#9C27B0', gradient: 'from-[#9C27B0] to-[#BA68C8]', light: '#F3E5F5' };
      case 'Signature':
        return { border: '#4A6CF7', bg: 'rgba(74, 108, 247, 0.15)', text: '#4A6CF7', gradient: 'from-[#4A6CF7] to-[#7B89F9]', light: '#F0F2FF' };
      case 'Stamp':
        return { border: '#F44336', bg: 'rgba(244, 67, 54, 0.15)', text: '#F44336', gradient: 'from-[#F44336] to-[#EF5350]', light: '#FFEBEE' };
    }
  };

  const handleDetectionClick = (detection: Detection) => {
    setSelectedPage(detection.pageNumber - 1);
    setSelectedDetection(detection.id);
  };

  const getCurrentDetections = () => {
    switch (activeTab) {
      case 'QR-code':
        return allQrCodes;
      case 'Signature':
        return allSignatures;
      case 'Stamp':
        return allStamps;
    }
  };

  const getTabIcon = (tab: DetectionTab) => {
    switch (tab) {
      case 'QR-code':
        return QrCode;
      case 'Signature':
        return PenLine;
      case 'Stamp':
        return Stamp;
    }
  };

  const getTabLabel = (tab: DetectionTab) => {
    switch (tab) {
      case 'QR-code':
        return 'QR Codes';
      case 'Signature':
        return 'Signatures';
      case 'Stamp':
        return 'Stamps';
    }
  };

  const currentDetections = getCurrentDetections();
  const colors = getTypeColor(activeTab);

  return (
    <div className="max-w-[1800px] mx-auto px-6 py-8">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={onBack}
          className="mb-4 text-[#6B7280] hover:text-[#1A1A1A] -ml-2"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Documents
        </Button>
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-[#1A1A1A] mb-2">{document.name}</h2>
            <p className="text-[#6B7280]">
              Detection Results · {document.pages} pages · {document.detections} detections found
            </p>
          </div>
          <div className="flex items-center gap-3">
            {/* Display Options - Compact */}
            <div className="flex items-center gap-2 px-3 py-2 bg-white border border-[#E6E6E6] rounded-lg shadow-sm">
              <div className="flex items-center gap-1.5">
                <Switch
                  id="boxes"
                  checked={showBoxes}
                  onCheckedChange={setShowBoxes}
                  className="scale-75"
                />
                <Label htmlFor="boxes" className="text-[#6B7280] cursor-pointer text-sm">
                  Boxes
                </Label>
              </div>
              <div className="w-px h-4 bg-[#E6E6E6]" />
              <div className="flex items-center gap-1.5">
                <Switch
                  id="labels"
                  checked={showLabels}
                  onCheckedChange={setShowLabels}
                  disabled={!showBoxes}
                  className="scale-75"
                />
                <Label htmlFor="labels" className="text-[#6B7280] cursor-pointer text-sm">
                  Labels
                </Label>
              </div>
              <div className="w-px h-4 bg-[#E6E6E6]" />
              <div className="flex items-center gap-1.5">
                <Switch
                  id="conf"
                  checked={showConfidence}
                  onCheckedChange={setShowConfidence}
                  disabled={!showBoxes || !showLabels}
                  className="scale-75"
                />
                <Label htmlFor="conf" className="text-[#6B7280] cursor-pointer text-sm">
                  %
                </Label>
              </div>
            </div>
            
            <Button
              className="bg-gradient-to-r from-[#4A6CF7] to-[#7B89F9] hover:opacity-90 text-white rounded-lg shadow-md"
            >
              <Download className="w-4 h-4 mr-2" />
              Download Report
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-12 gap-5">
        {/* Left Sidebar - Page Thumbnails (Thinner - shows 4-5 pages) */}
        <div className="col-span-1">
          <Card className="border-[#E6E6E6] rounded-xl sticky top-6 shadow-sm">
            <CardHeader className="pb-2 px-2 pt-2">
              <CardTitle className="text-[#1A1A1A] text-xs text-center">Pages</CardTitle>
            </CardHeader>
            <CardContent className="px-1 pb-1">
              <div className="space-y-1.5 max-h-[calc(100vh-200px)] overflow-y-auto">
                {pages.map((page, index) => (
                  <button
                    key={page.pageNumber}
                    onClick={() => setSelectedPage(index)}
                    className={`
                      w-full aspect-[8.5/11] rounded overflow-hidden border-2 transition-all
                      ${selectedPage === index 
                        ? 'border-[#4A6CF7] shadow-md ring-1 ring-[#4A6CF7]/30' 
                        : 'border-[#E6E6E6] hover:border-[#7B89F9]'
                      }
                    `}
                  >
                    <div className="relative w-full h-full">
                      <ImageWithFallback
                        src={page.imageUrl}
                        alt={`Page ${page.pageNumber}`}
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute inset-0 bg-black/5" />
                      <div className={`absolute bottom-0 right-0 px-1 py-0.5 text-xs ${selectedPage === index ? 'bg-[#4A6CF7] text-white' : 'bg-white/90 text-[#1A1A1A]'}`}>
                        {page.pageNumber}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Center - Document View */}
        <div className="col-span-8">
          <Card className="border-[#E6E6E6] rounded-xl shadow-sm">
            <CardHeader className="border-b border-[#E6E6E6] pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-[#1A1A1A]">
                  Page {currentPage.pageNumber}
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setZoom(Math.max(50, zoom - 25))}
                    disabled={zoom <= 50}
                    className="border-[#E6E6E6] rounded-lg disabled:opacity-50 h-9 w-9"
                  >
                    <ZoomOut className="w-4 h-4" />
                  </Button>
                  <span className="text-[#6B7280] min-w-[60px] text-center text-sm">
                    {zoom}%
                  </span>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setZoom(Math.min(200, zoom + 25))}
                    disabled={zoom >= 200}
                    className="border-[#E6E6E6] rounded-lg disabled:opacity-50 h-9 w-9"
                  >
                    <ZoomIn className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-4">
              <div 
                ref={documentContainerRef}
                className="bg-[#F7F8FA] rounded-lg p-4 flex items-start justify-center min-h-[calc(100vh-280px)] overflow-y-auto"
              >
                <div
                  className="relative bg-white shadow-lg rounded"
                  style={{
                    width: `${zoom}%`,
                    maxWidth: '100%'
                    // Removed fixed aspectRatio - let image determine its natural aspect ratio
                  }}
                >
                  <ImageWithFallback
                    src={currentPage.imageUrl}
                    alt={`Page ${currentPage.pageNumber}`}
                    className="w-full h-auto rounded"
                    style={{ display: 'block' }}
                  />
                  
                  {/* Detection Boxes */}
                  {showBoxes && currentPage.detections.map((detection) => {
                    const detectionColors = getTypeColor(detection.type);
                    const isSelected = selectedDetection === detection.id;
                    return (
                      <div
                        key={detection.id}
                        className="absolute group cursor-pointer transition-all"
                        style={{
                          left: `${detection.bbox.x}%`,
                          top: `${detection.bbox.y}%`,
                          width: `${detection.bbox.width}%`,
                          height: `${detection.bbox.height}%`,
                          border: `${isSelected ? '4' : '2'}px solid ${isSelected ? '#FFD700' : detectionColors.border}`,
                          backgroundColor: isSelected ? 'rgba(255, 215, 0, 0.2)' : detectionColors.bg,
                          boxShadow: isSelected 
                            ? '0 0 20px rgba(255, 215, 0, 0.8), 0 0 40px rgba(255, 215, 0, 0.5), 0 0 60px rgba(255, 215, 0, 0.3)' 
                            : 'none',
                          animation: isSelected ? 'pulse-gold 2s ease-in-out infinite' : 'none'
                        }}
                        onClick={() => setSelectedDetection(isSelected ? null : detection.id)}
                      >
                        {showLabels && (
                          <div
                            className="absolute -top-7 left-0 px-2 py-0.5 rounded text-white shadow-lg whitespace-nowrap text-xs"
                            style={{ backgroundColor: isSelected ? '#FFD700' : detectionColors.border }}
                          >
                            <span className="mr-1">{detection.type}</span>
                            {showConfidence && (
                              <span className="opacity-90">
                                ({(detection.confidence * 100).toFixed(0)}%)
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Sidebar - Detection Info */}
        <div className="col-span-3">
          <div className="sticky top-6">
            <Card className="border-[#E6E6E6] rounded-xl shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-[#1A1A1A]">All Detections</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Tab Menu Bar */}
                <div className="flex gap-2 p-1 bg-[#F7F8FA] rounded-lg">
                  {(['QR-code', 'Signature', 'Stamp'] as DetectionTab[]).map((tab) => {
                    const TabIcon = getTabIcon(tab);
                    const tabColors = getTypeColor(tab);
                    const isActive = activeTab === tab;
                    const count = tab === 'QR-code' ? allQrCodes.length : tab === 'Signature' ? allSignatures.length : allStamps.length;
                    
                    return (
                      <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`
                          flex-1 flex flex-col items-center gap-1 py-2 px-2 rounded-lg transition-all
                          ${isActive 
                            ? `bg-gradient-to-br ${tabColors.gradient} text-white shadow-md` 
                            : 'bg-white text-[#6B7280] hover:bg-white/80'
                          }
                        `}
                      >
                        <TabIcon className={`w-5 h-5 ${isActive ? 'text-white' : ''}`} style={{ color: isActive ? 'white' : tabColors.text }} />
                        <Badge 
                          className={`
                            text-xs px-2 py-0
                            ${isActive 
                              ? 'bg-white/20 text-white border-0' 
                              : 'bg-transparent border-0'
                            }
                          `}
                          style={{ color: isActive ? 'white' : tabColors.text }}
                        >
                          {count}
                        </Badge>
                      </button>
                    );
                  })}
                </div>

                {/* Detection List */}
                <div className="rounded-xl overflow-hidden border-2" style={{ borderColor: `${colors.border}30` }}>
                  <div 
                    className={`bg-gradient-to-r ${colors.gradient} text-white px-3 py-2 flex items-center justify-between`}
                  >
                    <span className="text-sm">{getTabLabel(activeTab)}</span>
                    <Badge className="bg-white/20 text-white border-0 text-xs">
                      {currentDetections.length}
                    </Badge>
                  </div>
                  <div className="bg-white max-h-[calc(100vh-450px)] overflow-y-auto">
                    {currentDetections.length > 0 ? (
                      <div className="divide-y divide-[#E6E6E6]">
                        {currentDetections.map((detection, idx) => {
                          const isSelected = selectedDetection === detection.id;
                          return (
                            <div
                              key={detection.id}
                              className={`
                                p-3 cursor-pointer transition-all
                                ${isSelected ? `border-l-4` : 'hover:bg-opacity-50'}
                              `}
                              style={{
                                backgroundColor: isSelected ? 'rgba(255, 215, 0, 0.1)' : 'transparent',
                                borderColor: isSelected ? '#FFD700' : 'transparent'
                              }}
                              onClick={() => handleDetectionClick(detection)}
                            >
                              <div className="flex items-center justify-between mb-1">
                                <span className={`${isSelected ? 'font-semibold' : ''}`} style={{ color: isSelected ? '#FFD700' : '#1A1A1A' }}>
                                  {getTabLabel(activeTab).slice(0, -1)} #{idx + 1}
                                </span>
                                <span className="text-[#6B7280] flex items-center gap-1 text-sm">
                                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                                  </svg>
                                  Page {detection.pageNumber}
                                </span>
                              </div>
                              {showConfidence && (
                                <div className="text-sm" style={{ color: isSelected ? '#FFD700' : colors.text }}>
                                  {(detection.confidence * 100).toFixed(0)}% confidence
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="p-8 text-center text-[#9CA3AF]">
                        No {getTabLabel(activeTab).toLowerCase()} found
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}