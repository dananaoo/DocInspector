import { useState } from 'react';
import { FileText, Trash2, Search, Calendar, Layers, QrCode, PenLine, Stamp } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Badge } from './ui/badge';
import type { Document } from '../App';

interface DocumentsListProps {
  documents: Document[];
  onOpenDocument: (id: number) => void;
  onDeleteDocument: (id: number) => void;
}

export function DocumentsList({ documents, onOpenDocument, onDeleteDocument }: DocumentsListProps) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredDocuments = documents.filter(doc =>
    doc.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getStatusColor = (status: Document['status']) => {
    switch (status) {
      case 'Processed':
        return 'bg-gradient-to-r from-[#E8F5E9] to-[#C8E6C9] text-[#2E7D32] border-[#3AB56C]/20';
      case 'In Queue':
        return 'bg-gradient-to-r from-[#FFF3E0] to-[#FFE0B2] text-[#F57C00] border-[#FFB74D]/20';
      case 'Error':
        return 'bg-gradient-to-r from-[#FFEBEE] to-[#FFCDD2] text-[#C62828] border-[#EF5350]/20';
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-[#1A1A1A] mb-2">Your Uploads</h2>
        <p className="text-[#6B7280]">
          View and manage all your uploaded documents
        </p>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#9CA3AF]" />
          <Input
            type="text"
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 bg-white border-[#E6E6E6] rounded-lg h-11"
          />
        </div>
      </div>

      {/* Documents Grid */}
      {filteredDocuments.length === 0 ? (
        <div className="bg-white rounded-xl border border-[#E6E6E6] p-12 text-center">
          <FileText className="w-12 h-12 text-[#D1D5DB] mx-auto mb-4" />
          <p className="text-[#6B7280]">
            {searchQuery ? 'No documents found' : 'No documents uploaded yet'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredDocuments.map((doc) => (
            <div
              key={doc.id}
              className="bg-white rounded-xl border border-[#E6E6E6] p-6 hover:shadow-md transition-all group"
            >
              <div className="flex items-start justify-between gap-4">
                {/* Left: Icon & Info */}
                <div className="flex items-start gap-4 flex-1 min-w-0">
                  <div className="w-12 h-12 rounded-lg bg-[#F0F2FF] flex items-center justify-center flex-shrink-0">
                    <FileText className="w-6 h-6 text-[#4A6CF7]" />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <h3 className="text-[#1A1A1A] mb-2 truncate">{doc.name}</h3>
                    
                    <div className="flex flex-wrap items-center gap-4 text-[#6B7280]">
                      <div className="flex items-center gap-1.5">
                        <Calendar className="w-4 h-4" />
                        <span>{new Date(doc.uploadDate).toLocaleDateString()}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Layers className="w-4 h-4" />
                        <span>{doc.pages} pages</span>
                      </div>
                      {doc.status === 'Processed' && (
                        <div className="flex items-center gap-1.5">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                          </svg>
                          <span>{doc.detections} detections</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Right: Status & Actions */}
                <div className="flex items-center gap-3 flex-shrink-0">
                  <Badge
                    variant="outline"
                    className={`${getStatusColor(doc.status)} border`}
                  >
                    {doc.status}
                  </Badge>

                  {/* Detection Icons - Show only for Processed documents */}
                  {doc.status === 'Processed' && (doc.qrCodes || doc.signatures || doc.stamps) && (
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-[#F7F8FA] rounded-lg border border-[#E6E6E6]">
                      {doc.qrCodes && doc.qrCodes > 0 && (
                        <div className="flex items-center gap-1">
                          <QrCode className="w-3.5 h-3.5 text-[#9C27B0]" />
                          <span className="text-[#9C27B0]">{doc.qrCodes}</span>
                        </div>
                      )}
                      {doc.signatures && doc.signatures > 0 && (
                        <div className="flex items-center gap-1">
                          <PenLine className="w-3.5 h-3.5 text-[#4A6CF7]" />
                          <span className="text-[#4A6CF7]">{doc.signatures}</span>
                        </div>
                      )}
                      {doc.stamps && doc.stamps > 0 && (
                        <div className="flex items-center gap-1">
                          <Stamp className="w-3.5 h-3.5 text-[#F44336]" />
                          <span className="text-[#F44336]">{doc.stamps}</span>
                        </div>
                      )}
                    </div>
                  )}

                  <Button
                    onClick={() => onOpenDocument(doc.id)}
                    disabled={doc.status !== 'Processed'}
                    className="bg-[#4A6CF7] hover:bg-[#7B89F9] text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Open
                  </Button>

                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => onDeleteDocument(doc.id)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity hover:bg-[#FFEBEE] hover:text-[#EF5350] rounded-lg"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}