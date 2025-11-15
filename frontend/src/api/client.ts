// API client for Digital Inspector backend
// Use relative URL in development (proxied by Vite), or full URL in production
const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export interface BackendDocument {
  id: number;
  filename: string;
  upload_date: string;
  total_pages: number;
  status: 'processing' | 'completed' | 'failed';
  created_at: string;
  summary?: {
    total_detections: number;
    by_class: {
      qr?: number;
      signature?: number;
      stamp?: number;
    };
  };
}

export interface BackendPage {
  page_id: number;
  page_number: number;
  document_id: number;
  detections_count: number;
}

export interface BackendDetection {
  id: number;
  class: string;  // Backend returns "class", not "class_name"
  confidence: number;
  bbox: {
    x1: number;
    y1: number;
    x2: number;
    y2: number;
    width: number;
    height: number;
  };
}

// Upload a document
export async function uploadDocument(file: File): Promise<{ document_id: number; filename: string; total_pages: number; status: string }> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error('Failed to upload document');
  }

  return response.json();
}

// Get all documents
export async function getDocuments(): Promise<BackendDocument[]> {
  const response = await fetch(`${API_BASE_URL}/api/documents`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch documents');
  }

  const data = await response.json();
  return data.documents || [];
}

// Get single document
export async function getDocument(id: number): Promise<BackendDocument> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${id}`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch document');
  }

  return response.json();
}

// Get pages for a document
export async function getDocumentPages(documentId: number): Promise<{ pages: BackendPage[] }> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/pages`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch pages');
  }

  return response.json();
}

// Get detections for a page
export async function getPageDetections(pageId: number): Promise<{ page_id: number; page_number: number; detections_count: number; detections: BackendDetection[] }> {
  const response = await fetch(`${API_BASE_URL}/api/pages/${pageId}/detections`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch detections');
  }

  return response.json();
}

// Get image URL for a page
export function getPageImageUrl(pageId: number): string {
  return `${API_BASE_URL}/api/pages/${pageId}/image`;
}

// Delete a document
export async function deleteDocument(id: number): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/documents/${id}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    throw new Error('Failed to delete document');
  }
}

// Poll document status until it's completed or failed
export async function pollDocumentStatus(
  documentId: number,
  onProgress?: (doc: BackendDocument) => void,
  maxAttempts: number = 60,
  intervalMs: number = 2000
): Promise<BackendDocument> {
  for (let i = 0; i < maxAttempts; i++) {
    const doc = await getDocument(documentId);
    
    if (onProgress) {
      onProgress(doc);
    }

    if (doc.status === 'completed' || doc.status === 'failed') {
      return doc;
    }

    await new Promise(resolve => setTimeout(resolve, intervalMs));
  }

  throw new Error('Document processing timeout');
}

