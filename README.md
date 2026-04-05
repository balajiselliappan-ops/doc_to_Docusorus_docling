# Document Converter

Convert PDF and DOCX documents to clean Markdown (MDX) and HTML using Docling, FastAPI, and Next.js.

## Features

- 📄 **PDF & DOCX Support**: Upload and convert both file formats
- 🖼️ **Image Extraction**: Automatically extracts and references images from documents
- 🎨 **Clean HTML Output**: Generates styled, responsive HTML previews
- ⚡ **FastAPI Backend**: High-performance document processing with Docling
- 🎯 **Next.js Frontend**: Modern React UI for upload and preview
- 📋 **Live Preview**: Real-time Markdown-to-HTML conversion in browser
- 💾 **Download Ready**: Export as Markdown, HTML, or plain text

## Project Structure

```
doc-to-docusaurus-docling/
├── backend/                    # FastAPI server
│   ├── parser.py              # Docling extraction & markdown conversion
│   ├── converter.py           # AI markdown cleanup & HTML generation
│   ├── cleaner.py             # Content sanitization
│   ├── main.py                # FastAPI routes (/upload/, /upload-layout/)
│   ├── uploads/               # Temporary uploaded files
│   ├── output/                # Generated markdown & HTML files
│   └── requirements.txt        # Python dependencies
├── frontend/                   # Next.js React app
│   ├── app/
│   │   ├── page.tsx           # Main upload & preview UI
│   │   ├── layout.tsx         # App wrapper
│   │   └── globals.css        # Tailwind styles
│   ├── package.json           # Node dependencies
│   └── tsconfig.json          # TypeScript config
└── README.md                  # This file
```

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- pip and npm

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (macOS/Linux)
source venv/bin/activate
# or Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run FastAPI server
uvicorn main:app --host 127.0.0.1 --port 8000
```

Server runs at `http://127.0.0.1:8000`
- API Docs: `http://127.0.0.1:8000/docs`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend runs at `http://localhost:3000`

## API Endpoints

### POST `/upload/`
Convert document to Markdown and HTML.

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/upload/ \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "markdown": "# Document Title\n...",
  "html": "<!doctype html>...",
  "engine": "docling",
  "output_file": "document.md",
  "html_output_file": "document.html",
  "image_count": 5,
  "image_asset_dir": "_docling_assets/document"
}
```

### POST `/upload-layout/`
Extract text with layout-aware formatting (PDF only).

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/upload-layout/ \
  -F "file=@document.pdf"
```

## File Outputs

- **Markdown**: `backend/output/{filename}.md`
- **HTML**: `backend/output/{filename}.html`
- **Images**: `_docling_assets/{doc-name}/*.png`
- **Uploaded Files**: `backend/uploads/{filename}`

## Configuration

### Backend

Edit `backend/parser.py` to adjust Docling settings:
```python
PdfPipelineOptions(
    generate_picture_images=True,  # Extract images from PDFs
    images_scale=2,                # Image resolution scale
)
```

### Frontend

Default backend URL in `frontend/app/page.tsx`:
```typescript
const DEFAULT_API_URL = "http://127.0.0.1:8000/upload/";
```

Change to match your backend deployment.

## Troubleshooting

### Images not loading in preview
- Check backend is running on correct port (8000)
- Verify image files exist in `backend/_docling_assets/`
- Restart frontend dev server to clear cache

### "Backend connection refused"
- Ensure FastAPI is running: `uvicorn main:app --host 127.0.0.1 --port 8000`
- Update API URL in frontend UI to match your backend

### Module not found errors (backend)
- Activate virtual environment: `source venv/bin/activate`
- Install all requirements: `pip install -r requirements.txt`
- Clear cache: `rm -rf __pycache__`

### Markdown conversion is incomplete
- Check `converter.py` logs for AI processing details
- Verify file format is supported (PDF, DOCX)
- Try a smaller document to isolate issues

## How It Works

### Conversion Pipeline

1. **Extraction** (`parser.py` / Docling)
   - Docling parses PDF/DOCX structure and layout
   - Extracts text, tables, and images with semantic understanding
   - Exports to clean Markdown with referenced images
   - For PDFs: generates high-quality images from content

2. **Cleaning** (`cleaner.py`)
   - Removes noise, malformed content, and artifacts
   - Normalizes whitespace and formatting
   - Extracts structured sections

3. **AI Enhancement** (`converter.py`)
   - Optional: processes Markdown through LLM for quality improvement
   - Handles large documents via intelligent chunking
   - Falls back to Pandoc if AI processing unavailable

4. **HTML Generation**
   - Converts Markdown to responsive HTML
   - Applies semantic styling
   - Preserves accessibility and readability

## About Docling

[Docling](https://github.com/DS4SD/docling) is IBM's document intelligence library that:

- **Understands document structure**: Tables, headers, footers, multi-column layouts
- **Extracts images intelligently**: Preserves diagrams and charts as referenced files
- **Handles multiple formats**: PDF, DOCX, HTML, and more
- **Generates clean Markdown**: Production-ready output without proprietary formatting

This project uses Docling's markdown export mode (`ImageRefMode.REFERENCED`) to create clean, portable Markdown with external image references—perfect for documentation sites and content management systems.

## Technologies

- **Extraction**: Docling (document intelligence)
- **Backend**: FastAPI, Python 3.9+
- **Frontend**: Next.js, React, TypeScript, Tailwind CSS
- **Fallback**: Pandoc (format conversion)
- **AI Enhancement**: OpenAI-compatible endpoints (optional, configurable)
- **HTML Styling**: Responsive CSS with semantic markup

## Development

### Running Both Services

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn main:app --host 127.0.0.1 --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Then open `http://localhost:3000`

## License

MIT

## Support

For issues, check:
1. Backend logs (terminal where FastAPI runs)
2. Browser console (F12 → Console tab)
3. Network tab (F12 → Network tab) for API request details
