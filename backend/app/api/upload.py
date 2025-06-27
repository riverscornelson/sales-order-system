from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List
import uuid
import structlog
import asyncio
from ..models.schemas import OrderProcessingSession, DocumentType, ProcessingStatus
from ..agents.simple_demo import SimpleDemoAgent
from ..services.websocket_manager import WebSocketManager

logger = structlog.get_logger()
router = APIRouter(tags=["upload"])

# WebSocket manager will be injected from main.py
websocket_manager = None
supervisor = None

async def process_document_background(session_id: str, client_id: str, filename: str, content: str):
    """Background task to process document through agent workflow"""
    logger.info("🚀 BACKGROUND TASK STARTED", session_id=session_id, client_id=client_id)
    try:
        # Initialize supervisor with OpenAI API key when needed
        global supervisor
        if supervisor is None:
            logger.info("📡 Initializing SIMPLE demo agent...")
            supervisor = SimpleDemoAgent(websocket_manager)
            logger.info("✅ SIMPLE demo agent initialized")
        
        logger.info("🤖 Starting agent workflow", filename=filename, content_length=len(content))
        await supervisor.process_document(session_id, client_id, filename, content)
        logger.info("✅ Document processing completed", session_id=session_id)
    except Exception as e:
        logger.error("❌ Document processing failed", session_id=session_id, error=str(e), exc_info=True)

@router.post("/upload")
async def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
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
    
    # Read file content
    content = await file.read()
    document_content = content.decode('utf-8') if doc_type == DocumentType.EMAIL else str(content)
    
    logger.info("📤 Document uploaded", 
               session_id=session_id, 
               filename=file.filename,
               content_type=file.content_type,
               content_size=len(content))
    
    logger.info("📋 Document content preview", 
               session_id=session_id,
               content_preview=document_content[:200] + "..." if len(document_content) > 200 else document_content)
    
    # Generate client ID for WebSocket connection
    client_id = f"client-{session_id}"
    
    # Start background processing through agent workflow
    logger.info("📋 Adding background task", session_id=session_id, client_id=client_id)
    background_tasks.add_task(
        process_document_background, 
        session_id, 
        client_id, 
        file.filename or "unknown", 
        document_content
    )
    logger.info("✅ Background task added successfully")
    
    return {
        "session_id": session_id,
        "client_id": client_id,
        "status": "uploaded",
        "message": "Document uploaded successfully. Multi-agent processing has started.",
        "filename": file.filename,
        "document_type": doc_type.value
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

# Debug endpoint to test background tasks
async def test_background_task():
    """Simple background task for testing"""
    logger.info("🧪 TEST BACKGROUND TASK STARTED")
    import asyncio
    await asyncio.sleep(1)
    logger.info("🧪 TEST BACKGROUND TASK COMPLETED")

@router.post("/test-background")
async def test_background(background_tasks: BackgroundTasks):
    """Test endpoint to verify background tasks work"""
    logger.info("🧪 Adding test background task")
    background_tasks.add_task(test_background_task)
    logger.info("🧪 Test background task added")
    return {"message": "Test background task started"}