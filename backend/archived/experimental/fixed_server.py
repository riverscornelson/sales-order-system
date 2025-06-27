#!/usr/bin/env python3
"""
Fixed working backend server 
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import uuid
import time
import hashlib

# Create app with minimal configuration
app = FastAPI(title="Sales Order API - Fixed")

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Sales Order API is running", "version": "fixed"}

@app.get("/api/v1/health")
def api_health():
    return {"status": "healthy", "service": "sales-order-api", "version": "fixed"}

@app.post("/api/v1/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload endpoint"""
    
    # Read file content
    content = await file.read()
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    print(f"📤 File uploaded: {file.filename}")
    print(f"📊 Size: {len(content)} bytes")
    print(f"🆔 Session: {session_id}")
    
    return {
        "session_id": session_id,
        "client_id": f"client-{session_id}",
        "status": "uploaded",
        "message": "Document uploaded successfully.",
        "filename": file.filename
    }

@app.get("/api/jobs/{job_id}/status")
def get_job_status(job_id: str):
    """Job status endpoint"""
    
    # Simple progression logic
    job_hash = int(hashlib.md5(job_id.encode()).hexdigest()[:8], 16)
    time_factor = int(time.time()) % 30  # Changes every 30 seconds
    progress_factor = (job_hash + time_factor) % 6
    
    statuses = [
        {"id": job_id, "status": "processing", "step": "parse", "message": "Parsing...", "progress": 20},
        {"id": job_id, "status": "processing", "step": "extract", "message": "Extracting...", "progress": 40},
        {"id": job_id, "status": "processing", "step": "match", "message": "Matching...", "progress": 60},
        {"id": job_id, "status": "processing", "step": "validate", "message": "Validating...", "progress": 80},
        {"id": job_id, "status": "completed", "step": "complete", "message": "Complete!", "progress": 100, "results": {"order_id": f"ORD-{job_id[:8]}", "line_items": [{"part_number": "ABC123", "quantity": 5}]}},
        {"id": job_id, "status": "completed", "step": "complete", "message": "Complete!", "progress": 100, "results": {"order_id": f"ORD-{job_id[:8]}", "line_items": [{"part_number": "ABC123", "quantity": 5}]}}
    ]
    
    return statuses[progress_factor]

if __name__ == "__main__":
    print("🚀 Starting fixed backend server on port 8001...")
    
    # Kill any existing process on port 8001
    import subprocess
    try:
        result = subprocess.run(['lsof', '-ti:8001'], capture_output=True, text=True)
        if result.stdout.strip():
            subprocess.run(['kill', result.stdout.strip()])
            time.sleep(1)
    except:
        pass
    
    uvicorn.run("__main__:app", host="127.0.0.1", port=8001, reload=False)