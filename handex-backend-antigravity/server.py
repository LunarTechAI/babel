import os
import shutil
import subprocess
import threading
import uuid
import time
import re
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# CORS configuration
origins = [
    "*",  # Allow all origins for development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
BASE_DIR = Path(__file__).parent
INPUTS_DIR = BASE_DIR / "Inputs"
OUTPUTS_DIR = BASE_DIR / "Outputs"
BABELDOC_DIR = BASE_DIR / "BabelDOC-main"
DASHBOARD_DIR = BASE_DIR.parent / "dashboard"

# Ensure directories exist
INPUTS_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

# Job tracking
jobs: Dict[str, dict] = {}

def load_env_file():
    """Load environment variables from .env file"""
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        print(f"Loading environment variables from {env_path}")
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    # Remove quotes if present
                    value = value.strip().strip("'").strip('"')
                    os.environ[key.strip()] = value
                    if key.strip() == "OPENAI_API_KEY":
                        print(f"Loaded OPENAI_API_KEY from .env (ends with ...{value[-4:]})")
    else:
        print(f"Warning: .env file not found at {env_path}")

# Load env vars on startup
load_env_file()

def run_translation_job(job_id: str, file_path: Path, target_language: str, openai_api_key: str):
    """Run translation in background thread"""
    try:
        # Update job status immediately with initial progress
        if job_id in jobs:
            jobs[job_id]["status"] = "processing"
            jobs[job_id]["progress"] = 3  # Start at 3% immediately
            jobs[job_id]["message"] = "File uploaded, preparing translation..."
            print(f"[Job {job_id}] Status updated: processing, progress: 3%")
        
        # Start progress simulator thread (fallback - will be overridden by actual BabelDOC stages)
        import threading
        stop_simulator = threading.Event()
        
        def simulate_progress():
            """Gradually increase progress over time as fallback if BabelDOC stages aren't detected"""
            # Fallback progress points (will be overridden by actual BabelDOC stage detection)
            progress_points = [
                (5, "Starting translation..."),           # 0-2s: Initial
                (10, "Parsing PDF document..."),          # 2-4s: Quick start
                (20, "Extracting content..."),            # 4-8s: Building confidence
                (30, "Extracting terminology..."),        # 8-12s
                (40, "Translating content..."),           # 12-16s
                (50, "Translating paragraphs..."),        # 16-20s
                (60, "Processing translation..."),        # 20-28s
                (70, "Formatting document..."),           # 28-40s
                (80, "Applying styles..."),               # 40-60s
                (85, "Generating PDF..."),                # 60-80s
                (90, "Optimizing output..."),             # 80-100s
                (95, "Finalizing..."),                    # 100-120s
            ]
            
            start_time = time.time()
            last_progress = 1  # Start from initial 1%
            
            for target_progress, message in progress_points:
                if stop_simulator.is_set():
                    break
                
                # Calculate time elapsed to adjust pacing
                elapsed = time.time() - start_time
                
                # Slower updates to avoid getting stuck at high percentages too early
                if target_progress <= 35:
                    sleep_time = 3  # Initial updates
                elif target_progress <= 75:
                    sleep_time = 6  # Medium speed
                else:
                    sleep_time = 10 # Much slower near completion
                
                time.sleep(sleep_time)
                
                if jobs[job_id]["status"] == "processing":
                    # Smoothly increase progress
                    jobs[job_id]["progress"] = target_progress
                    jobs[job_id]["message"] = message
                    print(f"[Job {job_id}] Progress: {target_progress}% - {message}")
                    last_progress = target_progress
        
        simulator_thread = threading.Thread(target=simulate_progress, daemon=True)
        simulator_thread.start()
        print(f"[Job {job_id}] Progress simulator thread started")
        
        cmd = [
            "uv", "run", "babeldoc",
            "--files", str(file_path.absolute()),
            "--lang-out", target_language,
            "--openai",
            "--openai-model", "gpt-4o",
            "--openai-api-key", openai_api_key,
            "--pool-max-workers", "4",  # Process with 4 parallel workers for faster translation
            "--output", str(OUTPUTS_DIR.absolute())
        ]
        
        print(f"[Job {job_id}] Running command: {' '.join(cmd)}")
        
        # Run BabelDOC
        process = subprocess.Popen(
            cmd,
            cwd=str(BABELDOC_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=dict(os.environ, PYTHONUNBUFFERED="1")
        )
        
        print(f"[Job {job_id}] BabelDOC process started with PID {process.pid}")
        
        # BabelDOC stage mapping to progress percentages
        babeldoc_stages = {
            "Loading ONNX model": (2, "Loading translation engine..."),
            "start to translate": (5, "Starting translation..."),
            "Parse PDF and Create Intermediate Representation": (10, "Parsing PDF document..."),
            "DetectScannedFile": (12, "Detecting document type..."),
            "Parse Page Layout": (18, "Analyzing page layout..."),
            "Parse Paragraphs": (25, "Extracting paragraphs..."),
            "Parse Formulas and Styles": (30, "Parsing formulas and styles..."),
            "Automatic Term Extraction": (35, "Extracting terminology..."),
            "Translate Paragraphs": (45, "Translating content..."),  # Main translation work
            "Typesetting": (75, "Formatting document..."),
            "Add Fonts": (82, "Adding fonts..."),
            "Generate drawing instructions": (88, "Generating graphics..."),
            "Subset font": (92, "Optimizing fonts..."),
            "Save PDF": (95, "Saving PDF..."),
            "finish translate": (97, "Finalizing translation..."),
            "Translation results": (98, "Translation complete!")
        }
        
        # Monitor output and detect BabelDOC stages
        # Use a buffer to handle fragmented output (e.g. single characters)
        output_buffer = ""
        
        while True:
            # Read one character at a time
            char = process.stdout.read(1)
            
            # If end of stream and process finished
            if not char and process.poll() is not None:
                break
                
            if not char:
                continue
                
            output_buffer += char
            
            # Process line if newline or carriage return detected
            if char == '\n' or char == '\r':
                line = output_buffer.strip()
                output_buffer = "" # Reset buffer
                
                if not line:
                    continue
                    
                print(f"[Job {job_id}] {line}")
                
                # Check for BabelDOC validation errors
                if "Cannot translate files that have already been translated" in line:
                    print(f"[Job {job_id}] Error detected: Input file is already a BabelDOC output")
                    jobs[job_id]["status"] = "failed"
                    jobs[job_id]["error"] = "Cannot translate a file that was already generated by BabelDOC. Please upload the original source file."
                    jobs[job_id]["message"] = "Error: File already translated"
                    process.kill()
                    return

                # Detect BabelDOC stages and update progress accordingly
                line_lower = line.lower()
                for stage_key, (progress, message) in babeldoc_stages.items():
                    if stage_key.lower() in line_lower:
                        if jobs[job_id]["status"] == "processing":
                            jobs[job_id]["progress"] = max(jobs[job_id].get("progress", 0), progress)
                            jobs[job_id]["message"] = message
                            print(f"[Job {job_id}] Stage detected: {stage_key} -> Progress: {progress}% - {message}")
                        break

                # Parse progress from output if available (fallback)
                if "%" in line:
                    match = re.search(r'(\d+)%', line)
                    if match:
                        progress = int(match.group(1))
                        # Only update if higher than current progress
                        if progress > jobs[job_id].get("progress", 0):
                            jobs[job_id]["progress"] = min(progress, 95)
        
        process.wait()
        
        # Stop simulator
        stop_simulator.set()
        
        if process.returncode != 0:
            stderr = process.stderr.read()
            print(f"[Job {job_id}] Error: {stderr}")
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = stderr
            jobs[job_id]["message"] = "Translation failed"
            return
        
        # Find output file - prioritize mono version over dual version
        input_stem = Path(jobs[job_id]["original_filename"]).stem
        
        # BabelDOC creates: filename.langcode.mono.pdf and filename.langcode.dual.pdf
        mono_pattern = f"{input_stem}.{target_language}.mono.pdf"
        dual_pattern = f"{input_stem}.{target_language}.dual.pdf"
        
        # Check for mono version first
        mono_file = OUTPUTS_DIR / mono_pattern
        if mono_file.exists():
            translated_file = mono_file
            print(f"[Job {job_id}] Found mono version: {mono_file.name}")
        else:
            # Fall back to finding any matching file, excluding dual versions
            all_files = list(OUTPUTS_DIR.glob(f"{input_stem}*.pdf"))
            if not all_files:
                all_files = list(OUTPUTS_DIR.glob(f"{input_stem}*"))
            
            if not all_files:
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = "Output file not found"
                jobs[job_id]["message"] = "Translation failed: output file not found"
                return
            
            # Filter out dual versions - prioritize mono
            mono_files = [f for f in all_files if '.mono.pdf' in f.name]
            if mono_files:
                potential_files = mono_files
                print(f"[Job {job_id}] Found {len(mono_files)} mono version(s)")
            else:
                # Filter out dual, get any remaining
                non_dual = [f for f in all_files if '.dual.pdf' not in f.name]
                if non_dual:
                    potential_files = non_dual
                    print(f"[Job {job_id}] Using non-dual version")
                else:
                    # Last resort: use dual
                    potential_files = all_files
                    print(f"[Job {job_id}] No mono version found, using dual as fallback")
            
            # Sort by modification time, newest first
            potential_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            translated_file = potential_files[0]
            print(f"[Job {job_id}] Selected file: {translated_file.name}")
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["translated_file"] = translated_file.name
        jobs[job_id]["message"] = "Translation complete!"
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        
        print(f"[Job {job_id}] Completed: {translated_file.name}")
        
    except Exception as e:
        print(f"[Job {job_id}] Exception: {str(e)}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["message"] = f"Translation failed: {str(e)}"

# Mount dashboard static files at /dashboard to match frontend paths
try:
    static_files = StaticFiles(directory=str(DASHBOARD_DIR), html=True)
    app.mount("/static", static_files, name="static") # Keep for backward compatibility
    app.mount("/dashboard", static_files, name="dashboard") # New standard path
    print(f"✓ Static files mounted at /dashboard and /static from {DASHBOARD_DIR}")
except Exception as e:
    print(f"✗ Warning: Could not mount static files: {e}")

@app.get("/")
async def root():
    """Redirect to dashboard index"""
    return RedirectResponse(url="/dashboard/index.html")

# Fallback redirects for common incorrect paths
@app.get("/front/index.html")
async def redirect_front():
    """Redirect old front path to dashboard"""
    return RedirectResponse(url="/dashboard/index.html", status_code=301)

@app.get("/upload")
async def redirect_upload():
    """Redirect /upload to upload page"""
    return RedirectResponse(url="/dashboard/upload-page/index.html", status_code=301)

@app.post("/api/translate")
async def translate_document(
    file: UploadFile = File(...),
    target_language: str = Form(...)
):
    try:
        # 1. Save uploaded file
        file_path = INPUTS_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. Check API key
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY environment variable is not set"
            )
        
        # 3. Create job
        job_id = str(uuid.uuid4())
        jobs[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "progress": 1,  # Start with 1% so progress bar shows immediately
            "original_filename": file.filename,
            "target_language": target_language,
            "translated_file": None,
            "error": None,
            "message": "Translation queued - starting...",
            "created_at": datetime.now().isoformat(),
            "completed_at": None
        }
        
        print(f"Created job {job_id} for {file.filename} -> {target_language}")
        
        # 4. Start background thread
        thread = threading.Thread(
            target=run_translation_job,
            args=(job_id, file_path, target_language, openai_api_key)
        )
        thread.daemon = True
        thread.start()
        
        # 5. Return job ID immediately
        return {
            "status": "success",
            "job_id": job_id,
            "message": "Translation started"
        }
    
    except Exception as e:
        print(f"Error creating job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    """Get translation job status"""
    if job_id not in jobs:
        print(f"[API] Job {job_id} not found in jobs dict")
        print(f"[API] Available jobs: {list(jobs.keys())[:5]}")
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    print(f"[API] Returning job {job_id}: status={job.get('status')}, progress={job.get('progress')}%")
    return job

@app.get("/api/translations")
async def list_translations():
    """List all translation jobs (for My Translations page)"""
    # Return all jobs, sorted by creation time (newest first)
    all_jobs = list(jobs.values())
    all_jobs.sort(key=lambda j: j.get("created_at", ""), reverse=True)
    return {"translations": all_jobs, "count": len(all_jobs)}

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    file_path = OUTPUTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@app.get("/api/view/{filename}")
async def view_file(filename: str):
    """Serve PDF for viewing in browser"""
    file_path = OUTPUTS_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=file_path,
        media_type='application/pdf',
        headers={
            'Content-Disposition': f'inline; filename="{filename}"'
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
