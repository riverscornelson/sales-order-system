# Enhanced logging configuration for Google Cloud
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

import structlog
from google.cloud import logging as cloud_logging
from structlog.processors import JSONRenderer

from .config import settings


class GoogleCloudLogHandler(logging.Handler):
    """Custom handler for Google Cloud Logging integration."""
    
    def __init__(self):
        super().__init__()
        if settings.ENVIRONMENT != "test":
            try:
                self.client = cloud_logging.Client()
                self.client.setup_logging()
            except Exception as e:
                print(f"Failed to setup Google Cloud Logging: {e}")
                self.client = None
        else:
            self.client = None
    
    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record to Google Cloud Logging."""
        if not self.client:
            return
        
        try:
            # Extract structured data if available
            extra_data = getattr(record, 'extra_data', {})
            
            # Create log entry
            log_entry = {
                'message': record.getMessage(),
                'severity': record.levelname,
                'timestamp': datetime.utcnow().isoformat(),
                'source_location': {
                    'file': record.filename,
                    'line': record.lineno,
                    'function': record.funcName
                },
                **extra_data
            }
            
            # Add trace context if available
            if hasattr(record, 'trace_id'):
                log_entry['trace'] = record.trace_id
            
            if hasattr(record, 'span_id'):
                log_entry['span_id'] = record.span_id
                
            # Log to Cloud Logging
            self.client.logger(record.name).log_struct(
                log_entry,
                severity=record.levelname
            )
            
        except Exception as e:
            # Fallback to stderr if Cloud Logging fails
            print(f"Failed to log to Google Cloud: {e}", file=sys.stderr)


def add_trace_context(logger, method_name, event_dict):
    """Add trace context from request if available."""
    # This will be populated by middleware
    trace_id = getattr(logger, '_trace_id', None)
    span_id = getattr(logger, '_span_id', None)
    
    if trace_id:
        event_dict['trace_id'] = trace_id
    if span_id:
        event_dict['span_id'] = span_id
        
    return event_dict


def add_service_context(logger, method_name, event_dict):
    """Add service context information."""
    event_dict.update({
        'service': 'sales-order-backend',
        'version': getattr(settings, 'VERSION', '1.0.0'),
        'environment': settings.ENVIRONMENT
    })
    return event_dict


def filter_sensitive_data(logger, method_name, event_dict):
    """Filter out sensitive information from logs."""
    sensitive_keys = {
        'password', 'secret', 'token', 'key', 'credential',
        'authorization', 'auth', 'api_key', 'openai_api_key'
    }
    
    def clean_dict(d: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(d, dict):
            return d
            
        cleaned = {}
        for k, v in d.items():
            key_lower = k.lower()
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                cleaned[k] = "[REDACTED]"
            elif isinstance(v, dict):
                cleaned[k] = clean_dict(v)
            elif isinstance(v, list):
                cleaned[k] = [clean_dict(item) if isinstance(item, dict) else item for item in v]
            else:
                cleaned[k] = v
        return cleaned
    
    return clean_dict(event_dict)


def setup_logging():
    """Configure structured logging for the application."""
    
    # Configure processors based on environment
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        add_service_context,
        add_trace_context,
        filter_sensitive_data,
    ]
    
    if settings.ENVIRONMENT == "development":
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True)
        ])
    else:
        processors.extend([
            structlog.processors.dict_tracebacks,
            JSONRenderer()
        ])
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    )
    
    # Add Google Cloud handler if not in development
    if settings.ENVIRONMENT != "development":
        root_logger = logging.getLogger()
        cloud_handler = GoogleCloudLogHandler()
        root_logger.addHandler(cloud_handler)
    
    # Set levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)


# Performance logging decorator
def log_performance(func_name: Optional[str] = None):
    """Decorator to log function performance metrics."""
    def decorator(func):
        import time
        from functools import wraps
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.time()
            function_name = func_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    "Function completed",
                    function=function_name,
                    duration_ms=round(duration * 1000, 2),
                    status="success"
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    "Function failed",
                    function=function_name,
                    duration_ms=round(duration * 1000, 2),
                    error=str(e),
                    status="error"
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.time()
            function_name = func_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(
                    "Function completed",
                    function=function_name,
                    duration_ms=round(duration * 1000, 2),
                    status="success"
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(
                    "Function failed",
                    function=function_name,
                    duration_ms=round(duration * 1000, 2),
                    error=str(e),
                    status="error"
                )
                raise
        
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Request logging context manager
class RequestLoggingContext:
    """Context manager for request-specific logging context."""
    
    def __init__(self, request_id: str, user_id: Optional[str] = None, trace_id: Optional[str] = None):
        self.request_id = request_id
        self.user_id = user_id
        self.trace_id = trace_id
        self.logger = get_logger("request")
        
    def __enter__(self):
        self.logger = self.logger.bind(
            request_id=self.request_id,
            user_id=self.user_id,
            trace_id=self.trace_id
        )
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.logger.error(
                "Request failed",
                exception=str(exc_val),
                exception_type=exc_type.__name__
            )
        else:
            self.logger.info("Request completed successfully")


# Application metrics logger
class MetricsLogger:
    """Logger for application metrics and business events."""
    
    def __init__(self):
        self.logger = get_logger("metrics")
    
    def log_document_processed(self, 
                              document_type: str, 
                              processing_time: float,
                              success: bool,
                              error: Optional[str] = None):
        """Log document processing metrics."""
        self.logger.info(
            "Document processed",
            metric_type="document_processing",
            document_type=document_type,
            processing_time_ms=round(processing_time * 1000, 2),
            success=success,
            error=error
        )
    
    def log_order_created(self, 
                         order_id: str,
                         customer_id: str,
                         line_items_count: int,
                         total_amount: Optional[float] = None):
        """Log order creation metrics."""
        self.logger.info(
            "Order created",
            metric_type="order_creation",
            order_id=order_id,
            customer_id=customer_id,
            line_items_count=line_items_count,
            total_amount=total_amount
        )
    
    def log_erp_integration(self,
                           operation: str,
                           provider: str,
                           success: bool,
                           response_time: float,
                           error: Optional[str] = None):
        """Log ERP integration metrics."""
        self.logger.info(
            "ERP integration",
            metric_type="erp_integration",
            operation=operation,
            provider=provider,
            success=success,
            response_time_ms=round(response_time * 1000, 2),
            error=error
        )
    
    def log_semantic_search(self,
                           query: str,
                           results_count: int,
                           search_time: float,
                           confidence_scores: list):
        """Log semantic search metrics."""
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        self.logger.info(
            "Semantic search performed",
            metric_type="semantic_search",
            query_length=len(query),
            results_count=results_count,
            search_time_ms=round(search_time * 1000, 2),
            avg_confidence=round(avg_confidence, 3)
        )


# Initialize metrics logger instance
metrics_logger = MetricsLogger()