#!/usr/bin/env python3
"""
Minimal FastAPI server to test basic functionality
"""
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Minimal Sales Order API")

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
    return {"message": "Sales Order API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "API is working"}

@app.get("/api/v1/health")
async def api_health():
    return {"status": "healthy", "service": "sales-order-api", "version": "1.0.0"}

@app.post("/api/v1/upload")
async def upload_file(file: UploadFile = File(...)):
    """Simple upload endpoint"""
    content = await file.read()
    
    return {
        "message": "File uploaded successfully",
        "filename": file.filename,
        "size": len(content),
        "content_type": file.content_type,
        "session_id": "test-session-123"
    }

@app.get("/api/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """Simple job status endpoint"""
    return {
        "id": job_id,
        "status": "completed",
        "step": "complete",
        "message": "Processing complete!",
        "progress": 100,
        "timestamp": "2025-01-01T00:00:00Z",
        "results": {
            "order_id": f"ORD-{job_id[:8]}",
            "line_items": [
                {"part_number": "ABC123", "quantity": 5, "description": "Sample part"}
            ]
        }
    }

if __name__ == "__main__":
    print("🚀 Starting minimal backend server...")
    print("🌐 Server will be available at: http://127.0.0.1:8000")
    print("📚 Health check: http://127.0.0.1:8000/health")
    print("📋 API health: http://127.0.0.1:8000/api/v1/health")
    
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="info")