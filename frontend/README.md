
  # Digital Inspector - Frontend

  React + TypeScript frontend for Digital Inspector, an AI-powered document analysis tool that detects signatures, stamps, and QR codes in construction documents.

  ## Features

  - 📤 **Upload PDFs** - Drag-and-drop or browse to upload documents
  - 🔍 **Real-time Detection** - View signatures, stamps, and QR codes detected by AI
  - 📊 **Interactive Visualization** - Zoom, toggle boxes, and click on detections
  - 📄 **Multi-page Support** - Navigate through all pages of your document
  - 💾 **Document Management** - List, view, and delete uploaded documents

  ## Prerequisites

  - Node.js 18+ and npm
  - Backend API running on `http://localhost:8000` (see `../backend/README.md`)

  ## Quick Start

  ### 1. Install Dependencies

  ```bash
  npm install
  ```

  ### 2. Configure API URL (Optional)

  For development, the Vite proxy is configured to forward API requests to `http://localhost:8000`.

  For production, create a `.env` file:

  ```bash
  cp .env.example .env
  # Edit .env and set VITE_API_URL=https://your-api-domain.com
  ```

  ### 3. Start the Backend API

  Make sure the backend is running first:

  ```bash
  cd ../backend
  python api_v2.py
  ```

  ### 4. Start the Development Server

  ```bash
  npm run dev
  ```

  The app will open at `http://localhost:3000`

  ## Project Structure

  ```
  frontend/
  ├── src/
  │   ├── api/
  │   │   └── client.ts          # API client for backend
  │   ├── components/
  │   │   ├── HomePage.tsx        # Upload page
  │   │   ├── DocumentsList.tsx   # Document list page
  │   │   ├── DocumentView.tsx    # Document viewer with detections
  │   │   └── ui/                 # shadcn/ui components
  │   ├── App.tsx                 # Main app component
  │   ├── main.tsx                # Entry point
  │   └── index.css               # Global styles
  ├── vite.config.ts              # Vite configuration with proxy
  └── package.json
  ```

  ## How It Works

  ### 1. Upload Flow

  ```
  User uploads PDF → POST /api/documents/upload
  → Backend processes document (background task)
  → Frontend polls status until complete
  → Displays detections when ready
  ```

  ### 2. View Flow

  ```
  User clicks document → GET /api/documents/{id}/pages
  → For each page: GET /api/pages/{page_id}/detections
  → Display annotated images from /api/pages/{page_id}/image
  → Render bounding boxes on images
  ```

  ### 3. Key API Endpoints Used

  | Endpoint | Purpose |
  |----------|---------|
  | `POST /api/documents/upload` | Upload PDF |
  | `GET /api/documents` | List all documents |
  | `GET /api/documents/{id}` | Get document details |
  | `GET /api/documents/{id}/pages` | Get pages for a document |
  | `GET /api/pages/{id}/detections` | Get detections for a page |
  | `GET /api/pages/{id}/image` | Get annotated image (generated on-demand) |
  | `DELETE /api/documents/{id}` | Delete document |

  ## Development

  ### Tech Stack

  - **React 18** - UI framework
  - **TypeScript** - Type safety
  - **Vite** - Build tool
  - **Tailwind CSS** - Styling
  - **shadcn/ui** - UI components
  - **Lucide React** - Icons
  - **Sonner** - Toast notifications

  ### Building for Production

  ```bash
  npm run build
  ```

  This creates an optimized build in the `build/` directory.

  ### Environment Variables

  - `VITE_API_URL` - Backend API URL (leave empty for dev with proxy)

  ## Troubleshooting

  ### Backend Connection Issues

  **Problem**: API calls fail with network errors

  **Solution**:
  1. Ensure backend is running: `cd ../backend && python api_v2.py`
  2. Check backend is on `http://localhost:8000`
  3. Check browser console for CORS errors

  ### No Detections Showing

  **Problem**: Document uploads but no detections appear

  **Solution**:
  1. Wait for processing to complete (status changes to "Processed")
  2. Check backend logs for errors
  3. Ensure backend is using the trained model (`best.pt`)

  ### Images Not Loading

  **Problem**: Page images don't load in document viewer

  **Solution**:
  1. Check backend API is returning images: `curl http://localhost:8000/api/pages/1/image`
  2. Check browser console for 404 errors
  3. Ensure document has been fully processed

  ## Credits

  Original Figma design: https://www.figma.com/design/9EiGZQfL5ErrZJP4FD46ay/Digital-Inspector-Web-Design
  