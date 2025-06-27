from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import structlog
from typing import List
import json
import time

from .api import health, orders, upload
from .services.websocket_manager import WebSocketManager
from .core.logging import setup_logging, get_logger
from .core.monitoring import performance_monitor, health_monitor
from .core.config import settings
from .middleware.logging import (
    LoggingMiddleware, 
    HealthCheckMiddleware, 
    PerformanceMiddleware,
    SecurityLoggingMiddleware
)

# Initialize logging
setup_logging()
logger = get_logger("main")

# Lifespan manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Sales Order Entry System starting up", version="1.0.0")
    
    # Register health checks
    async def database_health():
        try:
            # This would check database connectivity
            return {"healthy": True, "details": {"status": "connected"}}
        except Exception as e:
            return {"healthy": False, "details": {"error": str(e)}}
    
    async def external_services_health():
        try:
            # This would check external service connectivity
            return {"healthy": True, "details": {"services": ["openai", "vertex_ai"]}}
        except Exception as e:
            return {"healthy": False, "details": {"error": str(e)}}
    
    health_monitor.register_health_check("database", database_health)
    health_monitor.register_health_check("external_services", external_services_health)
    
    yield
    
    # Shutdown
    logger.info("Sales Order Entry System shutting down")

app = FastAPI(
    title="Sales Order Entry System",
    description="Multi-agent system for processing customer orders from emails and PDFs",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration based on environment
cors_origins = ["*"] if settings.ENVIRONMENT == "development" else [
    "https://*.run.app",  # Cloud Run URLs
    settings.FRONTEND_URL
] if hasattr(settings, 'FRONTEND_URL') else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add monitoring and logging middleware
app.add_middleware(SecurityLoggingMiddleware)
app.add_middleware(PerformanceMiddleware, slow_request_threshold=5.0)
app.add_middleware(LoggingMiddleware, exclude_paths={"/health", "/metrics", "/favicon.ico"})
app.add_middleware(HealthCheckMiddleware)

websocket_manager = WebSocketManager()

# Inject WebSocket manager into upload module
from .api import upload
upload.websocket_manager = websocket_manager

# Include API routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get application metrics for monitoring."""
    from .core.monitoring import metrics_collector
    return metrics_collector.get_metrics_summary()

# Enhanced health check endpoint
@app.get("/health")
async def enhanced_health_check():
    """Enhanced health check with dependency status."""
    health_status = await health_monitor.check_health()
    return health_status

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates."""
    await websocket_manager.connect(websocket, client_id)
    logger.info("WebSocket connected", client_id=client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            await websocket_manager.send_personal_message(
                f"Message received: {data}", client_id
            )
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)
        logger.info("WebSocket disconnected", client_id=client_id)

# Request monitoring middleware
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    """Monitor HTTP requests for performance metrics."""
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    
    # Record metrics
    performance_monitor.record_request_metrics(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=duration
    )
    
    return response

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)