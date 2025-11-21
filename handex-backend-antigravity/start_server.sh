#!/bin/bash
cd "$(dirname "$0")"
echo "Starting Handex FastAPI Server..."
echo "Server will be available at: http://localhost:8000"
echo "Dashboard will be available at: http://localhost:8000/"
echo ""
python3 server.py
