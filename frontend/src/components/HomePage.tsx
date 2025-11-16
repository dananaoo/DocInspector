import { useState, useRef } from 'react';
import { Upload, FileText } from 'lucide-react';
import { Button } from './ui/button';

interface HomePageProps {
  onUpload: (file: File) => void;
}

export function HomePage({ onUpload }: HomePageProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    const validFiles = files.filter(file => 
      file.type === 'application/pdf'
    );
    
    if (validFiles.length > 0) {
      // Upload up to 10 files
      const filesToUpload = validFiles.slice(0, 10);
      filesToUpload.forEach(file => onUpload(file));
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const validFiles = files.filter(file => 
      file.type === 'application/pdf'
    );
    
    if (validFiles.length > 0) {
      // Upload up to 10 files
      const filesToUpload = validFiles.slice(0, 10);
      filesToUpload.forEach(file => onUpload(file));
    }
    
    // Reset input to allow selecting the same files again
    if (e.target) {
      e.target.value = '';
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-16">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h2 className="text-[#1A1A1A] mb-3">Upload your document</h2>
          <p className="text-[#6B7280]">
            Supported format: PDF. Automatically detects signatures, stamps, and QR codes.
          </p>
        </div>

        {/* Upload Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            bg-white rounded-xl border-2 border-dashed p-12 text-center
            transition-all duration-200 shadow-sm
            ${
              isDragging
                ? 'border-[#4A6CF7] bg-[#F0F2FF] shadow-lg'
                : 'border-[#E6E6E6] hover:border-[#7B89F9]'
            }
          `}
        >
          <div className="flex flex-col items-center gap-6">
            {/* Icon */}
            <div className={`
              w-20 h-20 rounded-full flex items-center justify-center
              transition-colors duration-200
              ${isDragging ? 'bg-[#4A6CF7]' : 'bg-[#F0F2FF]'}
            `}>
              <Upload className={`w-10 h-10 ${isDragging ? 'text-white' : 'text-[#4A6CF7]'}`} />
            </div>

            {/* Text */}
            <div>
              <p className="text-[#1A1A1A] mb-2">
                Drag and drop your files here (up to 10 PDFs)
              </p>
              <p className="text-[#9CA3AF]">
                or
              </p>
            </div>

            {/* Button */}
            <Button
              onClick={handleButtonClick}
              className="bg-[#4A6CF7] hover:bg-[#7B89F9] text-white px-8 py-6 rounded-lg shadow-sm transition-all"
            >
              <FileText className="w-5 h-5 mr-2" />
              Browse Files
            </Button>

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              onChange={handleFileSelect}
              multiple
              className="hidden"
            />
          </div>
        </div>

        {/* Info Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
          <div className="bg-gradient-to-br from-[#4A6CF7] to-[#7B89F9] rounded-lg p-6 text-white shadow-md">
            <div className="w-10 h-10 rounded-lg bg-white/20 flex items-center justify-center mb-3">
              <Upload className="w-5 h-5 text-white" />
            </div>
            <h3 className="mb-2">Fast Upload</h3>
            <p className="text-white/90">
              Quick processing with instant results
            </p>
          </div>

          <div className="bg-gradient-to-br from-[#F44336] to-[#EF5350] rounded-lg p-6 text-white shadow-md">
            <div className="w-10 h-10 rounded-lg bg-white/20 flex items-center justify-center mb-3">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 className="mb-2">AI Detection</h3>
            <p className="text-white/90">
              Advanced model for accurate results
            </p>
          </div>

          <div className="bg-gradient-to-br from-[#9C27B0] to-[#BA68C8] rounded-lg p-6 text-white shadow-md">
            <div className="w-10 h-10 rounded-lg bg-white/20 flex items-center justify-center mb-3">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="mb-2">Secure</h3>
            <p className="text-white/90">
              Your documents are safe and private
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}