#!/usr/bin/env python3
"""
Entry point for the FastAPI DDD application.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

# Import from the src directory
from src.main import app as fastapi_app

# Export the app for uvicorn
app = fastapi_app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True, log_level="info")
