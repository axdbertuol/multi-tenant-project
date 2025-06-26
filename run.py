#!/usr/bin/env python3
"""
Alternative entry point that can be used with uvicorn directly.
Usage: uvicorn run:app --reload
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import app

# This allows running with: uvicorn run:app --reload