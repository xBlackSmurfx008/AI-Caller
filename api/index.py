"""
Vercel serverless function entry point for FastAPI application
This file is used by Vercel to deploy the FastAPI backend
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app (not the Socket.IO wrapped version for Vercel)
from src.main import fastapi_app

# Export the app for Vercel
app = fastapi_app

