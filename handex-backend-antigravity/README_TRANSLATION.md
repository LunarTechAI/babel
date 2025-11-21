# Handex Translation Backend Setup

## Overview
This backend connects the Handex dashboard to BabelDOC for document translation using GPT-4o.

## Prerequisites

1. **Python 3.8+** installed
2. **uv** package manager installed (for BabelDOC)
3. **OpenAI API Key** set as environment variable

## Setup

### 1. Install Dependencies

```bash
cd handex-backend-antigravity
pip install fastapi uvicorn python-multipart
```

### 2. Set OpenAI API Key

```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or add to your shell profile (`~/.zshrc` or `~/.bashrc`):
```bash
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### 3. Verify BabelDOC Installation

The backend uses BabelDOC which should be installed via `uv` in the `BabelDOC-main` directory.

## Starting the Server

```bash
cd handex-backend-antigravity
python3 server.py
```

The server will start on `http://localhost:8000`

## API Endpoints

### POST `/api/translate`
Upload a document for translation.

**Request:**
- `file`: PDF or DOCX file (multipart/form-data)
- `target_language`: Language code (e.g., "es", "fr", "de")

**Response:**
```json
{
  "status": "success",
  "job_id": "uuid-here",
  "message": "Translation started"
}
```

### GET `/api/job/{job_id}`
Get translation job status.

**Response:**
```json
{
  "job_id": "uuid-here",
  "status": "processing|completed|failed",
  "progress": 75,
  "message": "Translating content...",
  "original_filename": "document.pdf",
  "target_language": "es",
  "translated_file": "document.es.mono.pdf",
  "error": null
}
```

### GET `/api/translations`
List all translation jobs.

### GET `/api/download/{filename}`
Download a translated file.

### GET `/api/view/{filename}`
View a translated PDF in browser.

## Translation Flow

1. User uploads file on `/static/upload-page/index.html`
2. Frontend sends POST to `/api/translate`
3. Backend creates job and starts BabelDOC in background
4. Frontend redirects to `/static/translation-progress/index.html?job={job_id}`
5. Progress page polls `/api/job/{job_id}` every 2 seconds
6. When complete, redirects to `/static/translation-complete/index.html?file={filename}`

## BabelDOC Configuration

- **Model**: GPT-4o
- **Workers**: 4 parallel workers
- **Input**: `handex-backend-antigravity/Inputs/`
- **Output**: `handex-backend-antigravity/Outputs/`

## Troubleshooting

### "OPENAI_API_KEY environment variable is not set"
- Make sure you've exported the API key: `export OPENAI_API_KEY="your-key"`

### "Cannot connect to backend"
- Ensure the server is running: `python3 server.py`
- Check it's on port 8000: `lsof -i :8000`

### Translation fails
- Check server logs for BabelDOC errors
- Verify the input file is a valid PDF/DOCX
- Ensure BabelDOC is properly installed with `uv`

