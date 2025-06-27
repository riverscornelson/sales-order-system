#!/usr/bin/env python3
"""
Working FastAPI server for testing upload functionality
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import uuid
import time

app = FastAPI(title="Sales Order API - Working Version")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Sales Order API is running", "version": "working"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "API is working"}

@app.get("/api/v1/health")
async def api_health():
    return {"status": "healthy", "service": "sales-order-api", "version": "working"}

@app.post("/api/v1/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload endpoint that works with the frontend"""
    
    # Validate file type
    if not file.content_type:
        raise HTTPException(status_code=400, detail="File type not specified")
    
    allowed_types = ["application/pdf", "text/plain", "message/rfc822", "application/octet-stream"]
    if file.content_type not in allowed_types:
        print(f"⚠️  Warning: Unsupported file type {file.content_type}, but proceeding anyway")
    
    # Read file content
    content = await file.read()
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    print(f"📤 File uploaded: {file.filename}")
    print(f"📊 Size: {len(content)} bytes")
    print(f"🆔 Session: {session_id}")
    
    # Return response that matches what frontend expects
    return {
        "session_id": session_id,
        "client_id": f"client-{session_id}",
        "status": "uploaded",
        "message": "Document uploaded successfully. Processing started.",
        "filename": file.filename,
        "document_type": "email" if file.content_type == "text/plain" else "pdf"
    }

@app.get("/api/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """Job status endpoint with progressive updates"""
    
    print(f"📊 Status requested for job: {job_id}")
    
    # Create a pseudo-random but deterministic progression based on job_id
    import hashlib
    job_hash = int(hashlib.md5(job_id.encode()).hexdigest()[:8], 16)
    time_factor = int(time.time()) % 60  # Changes every minute
    progress_factor = (job_hash + time_factor) % 6
    
    statuses = [
        {
            "id": job_id, 
            "status": "processing", 
            "step": "parse", 
            "message": "Parsing document...", 
            "progress": 20, 
            "timestamp": "2025-01-01T00:00:00Z"
        },
        {
            "id": job_id, 
            "status": "processing", 
            "step": "extract", 
            "message": "Extracting line items...", 
            "progress": 40, 
            "timestamp": "2025-01-01T00:00:00Z"
        },
        {
            "id": job_id, 
            "status": "processing", 
            "step": "match", 
            "message": "Matching parts...", 
            "progress": 60, 
            "timestamp": "2025-01-01T00:00:00Z"
        },
        {
            "id": job_id, 
            "status": "processing", 
            "step": "validate", 
            "message": "Validating order...", 
            "progress": 80, 
            "timestamp": "2025-01-01T00:00:00Z"
        },
        {
            "id": job_id, 
            "status": "completed", 
            "step": "complete", 
            "message": "Processing complete!", 
            "progress": 100, 
            "timestamp": "2025-01-01T00:00:00Z", 
            "results": {
                "order_id": f"ORD-{job_id[:8]}", 
                "customer": "Sample Customer",
                "total_items": 3,
                "line_items": [
                    {"part_number": "ABC123", "quantity": 5, "description": "Sample part 1", "unit_price": 10.50},
                    {"part_number": "DEF456", "quantity": 2, "description": "Sample part 2", "unit_price": 25.00},
                    {"part_number": "GHI789", "quantity": 1, "description": "Sample part 3", "unit_price": 100.00}
                ]
            }
        },
        {
            "id": job_id, 
            "status": "completed", 
            "step": "complete", 
            "message": "Processing complete!", 
            "progress": 100, 
            "timestamp": "2025-01-01T00:00:00Z", 
            "results": {
                "order_id": f"ORD-{job_id[:8]}", 
                "customer": "Sample Customer",
                "total_items": 3,
                "line_items": [
                    {"part_number": "ABC123", "quantity": 5, "description": "Sample part 1", "unit_price": 10.50},
                    {"part_number": "DEF456", "quantity": 2, "description": "Sample part 2", "unit_price": 25.00},
                    {"part_number": "GHI789", "quantity": 1, "description": "Sample part 3", "unit_price": 100.00}
                ]
            }
        }
    ]
    
    return statuses[progress_factor]

if __name__ == "__main__":
    print("🚀 Starting working backend server...")
    print("🌐 Server will be available at: http://127.0.0.1:8001")
    print("📚 Health check: http://127.0.0.1:8001/health")
    print("📋 API health: http://127.0.0.1:8001/api/v1/health")
    print("📤 Upload endpoint: http://127.0.0.1:8001/api/v1/upload")
    
    # Kill the simple server first
    import subprocess
    import signal
    import os
    
    try:
        # Find and kill the simple test server
        result = subprocess.run(['lsof', '-ti:8001'], capture_output=True, text=True)
        if result.stdout.strip():
            pid = int(result.stdout.strip())
            os.kill(pid, signal.SIGTERM)
            print(f"🔌 Stopped existing server on port 8001 (PID: {pid})")
    except:
        pass
    
    time.sleep(1)  # Give it a moment to release the port
    
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")