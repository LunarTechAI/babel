#!/bin/bash

# Handex Translation Server Startup Script

cd "$(dirname "$0")"

echo "=========================================="
echo "Handex Translation Server"
echo "=========================================="
echo ""

# Check if OpenAI API key is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  WARNING: OPENAI_API_KEY is not set!"
    echo "   Set it with: export OPENAI_API_KEY='your-key-here'"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ OPENAI_API_KEY is set"
fi

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Check if required packages are installed
echo "Checking dependencies..."
python3 -c "import fastapi" 2>/dev/null || {
    echo "⚠️  FastAPI not found. Installing..."
    pip3 install fastapi uvicorn python-multipart
}

# Check if BabelDOC directory exists
if [ ! -d "BabelDOC-main" ]; then
    echo "⚠️  WARNING: BabelDOC-main directory not found!"
    echo "   Make sure BabelDOC is properly set up."
fi

echo ""
echo "Starting server on http://localhost:8000"
echo "Press CTRL+C to stop"
echo "=========================================="
echo ""

python3 server.py

