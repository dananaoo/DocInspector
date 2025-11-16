import { useState, useEffect } from 'react';
import { HomePage } from './components/HomePage';
import { DocumentsList } from './components/DocumentsList';
import { DocumentView } from './components/DocumentView';
import * as api from './api/client';
import { toast } from 'sonner';

type Page = 'home' | 'documents' | 'view';

export interface Document {
  id: number;
  name: string;
  uploadDate: string;
  status: 'Processed' | 'In Queue' | 'Error';
  pages: number;
  detections: number;
  qrCodes?: number;
  signatures?: number;
  stamps?: number;
}

// Convert backend document to frontend document
function convertDocument(doc: api.BackendDocument): Document {
  // Safely extract date
  let uploadDate = doc.upload_date || '';
  if (!uploadDate && doc.created_at) {
    uploadDate = doc.created_at.split('T')[0];
  }
  if (!uploadDate) {
    uploadDate = new Date().toISOString().split('T')[0];
  }

  return {
    id: doc.id,
    name: doc.filename,
    uploadDate,
    status: doc.status === 'completed' ? 'Processed' : doc.status === 'processing' ? 'In Queue' : 'Error',
    pages: doc.total_pages,
    detections: doc.summary?.total_detections || 0,
    qrCodes: doc.summary?.by_class?.qr || 0,
    signatures: doc.summary?.by_class?.signature || 0,
    stamps: doc.summary?.by_class?.stamp || 0,
  };
}

export default function App() {
  const [currentPage, setCurrentPage] = useState<Page>('home');
  const [selectedDocumentId, setSelectedDocumentId] = useState<number | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  // Load documents on mount
  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const backendDocs = await api.getDocuments();
      const converted = backendDocs.map(convertDocument);
      setDocuments(converted);
    } catch (error) {
      console.error('Failed to load documents:', error);
      toast.error('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (file: File) => {
    try {
      // Upload the file (this is async and can run in parallel with other uploads)
      const result = await api.uploadDocument(file);
      
      // Create a temporary document with 'In Queue' status
      const tempDoc: Document = {
        id: result.document_id,
        name: result.filename,
        uploadDate: new Date().toISOString().split('T')[0],
        status: 'In Queue',
        pages: result.total_pages,
        detections: 0
      };
      
      // Add to documents list immediately (optimistic update)
      const isFirstDocument = documents.length === 0;
      setDocuments(prev => [tempDoc, ...prev]);
      
      // Open the first uploaded document immediately (don't wait for others)
      // Always open if we're on home page, or if this is the first document
      if (currentPage === 'home' || isFirstDocument) {
        setSelectedDocumentId(result.document_id);
        setCurrentPage('view');
      }
      
      toast.success(`${result.filename} uploaded successfully!`);
      
      // Poll for completion in background (non-blocking)
      api.pollDocumentStatus(result.document_id, (doc) => {
        const converted = convertDocument(doc);
        setDocuments(prev => prev.map(d => d.id === converted.id ? converted : d));
      }).then((doc) => {
        const converted = convertDocument(doc);
        setDocuments(prev => prev.map(d => d.id === converted.id ? converted : d));
        // Only show toast if document is not currently being viewed
        if (selectedDocumentId !== doc.id) {
          toast.success(`${doc.filename} processing completed!`);
        }
      }).catch((error) => {
        console.error('Polling error:', error);
        // Don't show error toast for polling - it's background
      });
      
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(`Failed to upload ${file.name}`);
    }
  };

  const handleOpenDocument = (id: number) => {
    setSelectedDocumentId(id);
    setCurrentPage('view');
  };

  const handleDeleteDocument = async (id: number) => {
    try {
      await api.deleteDocument(id);
      setDocuments(documents.filter(doc => doc.id !== id));
      toast.success('Document deleted');
    } catch (error) {
      console.error('Delete failed:', error);
      toast.error('Failed to delete document');
    }
  };

  const selectedDocument = documents.find(doc => doc.id === selectedDocumentId);

  return (
    <div className="min-h-screen bg-[#F7F8FA]">
      {/* Navigation Bar */}
      <nav className="bg-white border-b border-[#E6E6E6] shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-8">
              <h1 
                className="text-[#1A1A1A] cursor-pointer flex items-center gap-2"
                onClick={() => setCurrentPage('home')}
              >
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#4A6CF7] to-[#7B89F9] flex items-center justify-center relative">
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    {/* Document */}
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <svg className="w-3 h-3 text-white absolute -bottom-0.5 -right-0.5 bg-gradient-to-br from-[#4A6CF7] to-[#7B89F9] rounded-full" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={3}>
                    {/* Search magnifier */}
                    <circle cx="11" cy="11" r="6" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35" />
                  </svg>
                </div>
                SignHunter
              </h1>
              <div className="flex gap-1">
                <button
                  onClick={() => setCurrentPage('home')}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    currentPage === 'home'
                      ? 'bg-gradient-to-r from-[#4A6CF7] to-[#7B89F9] text-white shadow-md'
                      : 'text-[#6B7280] hover:text-[#1A1A1A] hover:bg-[#F7F8FA]'
                  }`}
                >
                  Upload
                </button>
                <button
                  onClick={() => setCurrentPage('documents')}
                  className={`px-4 py-2 rounded-lg transition-colors ${
                    currentPage === 'documents' || currentPage === 'view'
                      ? 'bg-gradient-to-r from-[#4A6CF7] to-[#7B89F9] text-white shadow-md'
                      : 'text-[#6B7280] hover:text-[#1A1A1A] hover:bg-[#F7F8FA]'
                  }`}
                >
                  Documents
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main>
        {currentPage === 'home' && <HomePage onUpload={handleUpload} />}
        {currentPage === 'documents' && (
          <DocumentsList
            documents={documents}
            onOpenDocument={handleOpenDocument}
            onDeleteDocument={handleDeleteDocument}
          />
        )}
        {currentPage === 'view' && selectedDocument && (
          <DocumentView document={selectedDocument} onBack={() => setCurrentPage('documents')} />
        )}
      </main>
    </div>
  );
}