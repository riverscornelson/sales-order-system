#!/usr/bin/env python3
"""
Local development server for Sales Order Entry System
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment to development
os.environ.setdefault('ENVIRONMENT', 'development')
os.environ.setdefault('DEBUG', 'true')

# Create local data directories
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('uploads', exist_ok=True)

print("🚀 Starting Sales Order Entry System - Local Development")
print("=" * 60)
print(f"Project Root: {project_root}")
print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
print(f"Debug Mode: {os.getenv('DEBUG', 'true')}")
print("=" * 60)

if __name__ == "__main__":
    import uvicorn
    
    # Run the FastAPI application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )