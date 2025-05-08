#!/usr/bin/env python3
"""
Run script for the What Beats Rock? backend application.
"""

import os
import uvicorn
from dotenv import load_dotenv
from pathlib import Path

# Import modules to ensure they're loaded
from app import main, game_service, count_range_service

# Load environment variables from root directory
root_dir = Path(__file__).resolve().parent.parent  # Go up one level to reach the root directory
env_path = os.path.join(root_dir, '.env')
load_dotenv(dotenv_path=env_path)

if __name__ == "__main__":
    # Get port from environment variable or use default
    port = int(os.getenv("PORT", 8000))
    
    print(f"Starting What Beats Rock? backend on port {port}...")
    
    # Run the FastAPI application with Uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)