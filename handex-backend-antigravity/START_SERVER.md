# How to Start the Handex Server

## Quick Start

1. **Open Terminal** and navigate to the server directory:
   ```bash
   cd /Users/vaheaslanyan/Documents/Apps/Handex/handex-backend-antigravity
   ```

2. **Start the server**:
   ```bash
   python3 server.py
   ```

3. **You should see**:
   ```
   ✓ Static files mounted at /static from /Users/vaheaslanyan/Documents/Apps/Handex/dashboard
   INFO:     Started server process [xxxxx]
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
   ```

4. **Open your browser** and go to:
   - `http://localhost:8000/`
   - OR `http://127.0.0.1:8000/`

## Troubleshooting

### If you see "port already in use":
```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process (replace PID with the actual process ID)
kill -9 <PID>
```

### If the server doesn't start:
1. Make sure you're in the correct directory
2. Check if Python 3 is installed: `python3 --version`
3. Check if dependencies are installed: `pip3 list | grep fastapi`

### If you can't access localhost:8000:
1. Make sure the server is actually running (you should see the INFO messages)
2. Try `http://127.0.0.1:8000/` instead of `http://localhost:8000/`
3. Check your firewall settings
4. Make sure you're not using a proxy

### Alternative Start Method:
```bash
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

## Important Notes

- **DO NOT** use VS Code Live Preview (port 3004) - it won't work with the `/static/` paths
- **DO NOT** open HTML files directly from the filesystem (`file://`)
- You **MUST** access through the FastAPI server on port 8000
- The server must stay running - don't close the terminal window

