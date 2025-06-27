# Logging middleware for request tracing and monitoring
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger, RequestLoggingContext


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request logging and tracing."""
    
    def __init__(self, app, exclude_paths: set = None):
        super().__init__(app)
        self.logger = get_logger("middleware.logging")
        self.exclude_paths = exclude_paths or {"/health", "/metrics", "/favicon.ico"}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Generate request ID and extract trace information
        request_id = str(uuid.uuid4())
        trace_id = request.headers.get("x-cloud-trace-context", "").split("/")[0]
        user_id = None  # Extract from auth headers if available
        
        # Extract user info from authorization header if present
        auth_header = request.headers.get("authorization", "")
        if auth_header:
            # This would be customized based on your auth implementation
            user_id = "authenticated_user"  # Placeholder
        
        # Add request context to request state
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        request.state.user_id = user_id
        
        start_time = time.time()
        
        # Log request start
        with RequestLoggingContext(request_id, user_id, trace_id) as logger:
            logger.info(
                "Request started",
                method=request.method,
                path=request.url.path,
                query_params=dict(request.query_params),
                client_ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent", ""),
                content_type=request.headers.get("content-type", ""),
                content_length=request.headers.get("content-length", 0)
            )
            
            try:
                # Process request
                response = await call_next(request)
                
                # Calculate duration
                duration = time.time() - start_time
                
                # Log successful response
                logger.info(
                    "Request completed",
                    status_code=response.status_code,
                    duration_ms=round(duration * 1000, 2),
                    response_size=response.headers.get("content-length", 0)
                )
                
                # Add request ID to response headers
                response.headers["x-request-id"] = request_id
                if trace_id:
                    response.headers["x-trace-id"] = trace_id
                
                return response
                
            except Exception as e:
                duration = time.time() - start_time
                
                # Log error
                logger.error(
                    "Request failed with exception",
                    exception=str(e),
                    exception_type=type(e).__name__,
                    duration_ms=round(duration * 1000, 2)
                )
                
                # Re-raise the exception
                raise


class HealthCheckMiddleware(BaseHTTPMiddleware):
    """Lightweight middleware for health check endpoints."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # For health checks, just pass through without heavy processing
        if request.url.path in {"/health", "/readiness", "/liveness"}:
            start_time = time.time()
            response = await call_next(request)
            
            # Only log if health check fails
            if response.status_code >= 400:
                duration = time.time() - start_time
                logger = get_logger("health")
                logger.warning(
                    "Health check failed",
                    path=request.url.path,
                    status_code=response.status_code,
                    duration_ms=round(duration * 1000, 2)
                )
            
            return response
        
        return await call_next(request)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for performance monitoring and slow request detection."""
    
    def __init__(self, app, slow_request_threshold: float = 5.0):
        super().__init__(app)
        self.logger = get_logger("performance")
        self.slow_request_threshold = slow_request_threshold  # seconds
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        # Log slow requests
        if duration > self.slow_request_threshold:
            self.logger.warning(
                "Slow request detected",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration * 1000, 2),
                status_code=response.status_code,
                threshold_ms=self.slow_request_threshold * 1000
            )
        
        # Add performance headers
        response.headers["x-response-time"] = str(round(duration * 1000, 2))
        
        return response


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for security event logging."""
    
    def __init__(self, app):
        super().__init__(app)
        self.logger = get_logger("security")
        self.suspicious_patterns = {
            "sql_injection": ["union", "select", "drop", "delete", "insert", "--", ";"],
            "xss": ["<script", "javascript:", "onerror=", "onload="],
            "path_traversal": ["../", "..\\", "/etc/", "\\windows\\"],
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check for suspicious patterns in query parameters and path
        self._check_suspicious_activity(request)
        
        response = await call_next(request)
        
        # Log authentication failures
        if response.status_code == 401:
            self.logger.warning(
                "Authentication failure",
                method=request.method,
                path=request.url.path,
                client_ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent", "")
            )
        
        # Log authorization failures
        elif response.status_code == 403:
            self.logger.warning(
                "Authorization failure",
                method=request.method,
                path=request.url.path,
                client_ip=request.client.host if request.client else None,
                user_id=getattr(request.state, 'user_id', None)
            )
        
        return response
    
    def _check_suspicious_activity(self, request: Request):
        """Check for suspicious patterns in the request."""
        query_string = str(request.query_params).lower()
        path = request.url.path.lower()
        
        for attack_type, patterns in self.suspicious_patterns.items():
            for pattern in patterns:
                if pattern in query_string or pattern in path:
                    self.logger.warning(
                        "Suspicious activity detected",
                        attack_type=attack_type,
                        pattern=pattern,
                        method=request.method,
                        path=request.url.path,
                        query_params=dict(request.query_params),
                        client_ip=request.client.host if request.client else None,
                        user_agent=request.headers.get("user-agent", "")
                    )
                    break