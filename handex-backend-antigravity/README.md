# Handex System - Quick Start Guide

## Prerequisites
1. Set your OpenAI API key as an environment variable:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

## Starting the System

### 1. Start the Backend Server
```bash
cd /Users/vaheaslanyan/Documents/Apps/Handex/handex-backend-antigravity
python3 server.py
```

The server will start on `http://localhost:8000`

### 2. Open the Dashboard
Open the following file in your browser:
```
/Users/vaheaslanyan/Documents/Apps/Handex/dashboard/upload-page/index.html
```

## Using the Application

1. **Upload a Document**: Click "Upload File" or drag & drop a PDF/DOCX file
2. **Select Target Language**: Choose from the dropdown (Spanish, French, German, Japanese, Chinese)
3. **Translate**: Click "Translate Handbook" button
4. **Download**: The translated file will automatically download when ready

## System Architecture

```
┌─────────────────┐         HTTP POST          ┌──────────────────┐
│                 │  /api/translate (file)      │                  │
│   Dashboard     ├────────────────────────────▶│  FastAPI Server  │
│  (Frontend)     │                             │  (Backend)       │
│                 │◀────────────────────────────┤                  │
└─────────────────┘   JSON response + file URL  └────────┬─────────┘
                                                         │
                                                         │ subprocess
                                                         │
                                                         ▼
                                                  ┌──────────────┐
                                                  │  BabelDOC    │
                                                  │  CLI Engine  │
                                                  └──────────────┘
```

## API Endpoints

- `GET /` - Health check
- `POST /api/translate` - Upload and translate document
  - Parameters: `file` (multipart), `target_language` (string)
- `GET /api/download/{filename}` - Download translated file
