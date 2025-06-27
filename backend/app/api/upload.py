from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
import uuid
import structlog
from ..models.schemas import OrderProcessingSession, DocumentType, ProcessingStatus

logger = structlog.get_logger()
router = APIRouter(tags=["upload"])

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF or email file for order processing"""
    
    # Validate file type
    if not file.content_type:
        raise HTTPException(status_code=400, detail="File type not specified")
    
    allowed_types = ["application/pdf", "text/plain", "message/rfc822"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type: {file.content_type}"
        )
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    
    # Determine document type
    doc_type = DocumentType.PDF if file.content_type == "application/pdf" else DocumentType.EMAIL
    
    # Create processing session
    session = OrderProcessingSession(
        session_id=session_id,
        document_type=doc_type,
        filename=file.filename or "unknown",
        status=ProcessingStatus.PENDING
    )
    
    logger.info("Document uploaded", 
               session_id=session_id, 
               filename=file.filename,
               content_type=file.content_type)
    
    # TODO: Store file and initiate processing
    # For now, return session info
    
    return {
        "session_id": session_id,
        "status": "uploaded",
        "message": "Document uploaded successfully. Processing will begin shortly."
    }

@router.get("/sessions/{session_id}")
async def get_session_status(session_id: str):
    """Get the current status of a processing session"""
    
    # TODO: Retrieve session from database
    # For now, return mock data
    
    return {
        "session_id": session_id,
        "status": "processing",
        "message": "Session found"
    }