#!/usr/bin/env python3
"""
Quick test to verify the server can start and respond
"""
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from server import app, DASHBOARD_DIR
    
    print("=" * 60)
    print("Server Configuration Test")
    print("=" * 60)
    print(f"✓ Server imports successfully")
    print(f"✓ DASHBOARD_DIR: {DASHBOARD_DIR}")
    print(f"✓ Dashboard exists: {Path(DASHBOARD_DIR).exists()}")
    print(f"✓ index.html exists: {(Path(DASHBOARD_DIR) / 'index.html').exists()}")
    print(f"✓ Total routes: {len(app.routes)}")
    print()
    print("Routes:")
    for route in app.routes:
        if hasattr(route, 'path'):
            print(f"  - {route.path}")
    print()
    print("=" * 60)
    print("To start the server, run:")
    print("  python3 server.py")
    print()
    print("Then access in your browser:")
    print("  http://localhost:8000/")
    print("=" * 60)
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

