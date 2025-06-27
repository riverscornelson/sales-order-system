# Application monitoring and metrics collection
import time
from contextlib import contextmanager
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict, deque
import threading
import asyncio

from google.cloud import monitoring_v3
from google.api_core import exceptions as gcp_exceptions

from .config import settings
from .logging import get_logger


@dataclass
class MetricData:
    """Container for metric data."""
    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: Optional[float] = None
    unit: str = "1"


class MetricsCollector:
    """Collects and manages application metrics."""
    
    def __init__(self):
        self.logger = get_logger("monitoring.collector")
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._lock = threading.RLock()
        
        # Initialize Google Cloud Monitoring client
        self.client = None
        if settings.ENVIRONMENT != "test":
            try:
                self.client = monitoring_v3.MetricServiceClient()
                self.project_name = f"projects/{settings.GOOGLE_CLOUD_PROJECT}"
            except Exception as e:
                self.logger.warning(f"Failed to initialize Cloud Monitoring client: {e}")
    
    def record_metric(self, metric: MetricData):
        """Record a metric value."""
        if not metric.timestamp:
            metric.timestamp = time.time()
        
        with self._lock:
            self._metrics[metric.name].append(metric)
        
        # Send to Cloud Monitoring if available
        if self.client and settings.ENVIRONMENT != "development":
            asyncio.create_task(self._send_to_cloud_monitoring(metric))
    
    def increment_counter(self, name: str, labels: Dict[str, str] = None):
        """Increment a counter metric."""
        self.record_metric(MetricData(
            name=f"counter/{name}",
            value=1,
            labels=labels or {}
        ))
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a histogram value (typically for timing)."""
        self.record_metric(MetricData(
            name=f"histogram/{name}",
            value=value,
            labels=labels or {}
        ))
    
    def record_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a gauge value (current state)."""
        self.record_metric(MetricData(
            name=f"gauge/{name}",
            value=value,
            labels=labels or {}
        ))
    
    async def _send_to_cloud_monitoring(self, metric: MetricData):
        """Send metric to Google Cloud Monitoring."""
        if not self.client:
            return
        
        try:
            # Create time series data
            series = monitoring_v3.TimeSeries()
            series.metric.type = f"custom.googleapis.com/sales_order/{metric.name}"
            
            # Add labels
            for key, value in metric.labels.items():
                series.metric.labels[key] = str(value)
            
            # Set resource
            series.resource.type = "gce_instance"  # or "cloud_run_revision"
            
            # Add point
            point = monitoring_v3.Point()
            point.value.double_value = metric.value
            point.interval.end_time.seconds = int(metric.timestamp)
            series.points = [point]
            
            # Send to Cloud Monitoring
            self.client.create_time_series(
                name=self.project_name,
                time_series=[series]
            )
            
        except gcp_exceptions.GoogleAPIError as e:
            self.logger.warning(f"Failed to send metric to Cloud Monitoring: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error sending metric: {e}")
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of collected metrics."""
        with self._lock:
            summary = {}
            for name, values in self._metrics.items():
                if values:
                    values_list = [m.value for m in values]
                    summary[name] = {
                        "count": len(values_list),
                        "latest": values_list[-1],
                        "average": sum(values_list) / len(values_list),
                        "min": min(values_list),
                        "max": max(values_list)
                    }
            return summary


class PerformanceMonitor:
    """Monitor application performance metrics."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.logger = get_logger("monitoring.performance")
    
    @contextmanager
    def timer(self, name: str, labels: Dict[str, str] = None):
        """Context manager for timing operations."""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.metrics.record_histogram(
                f"operation_duration_seconds/{name}",
                duration,
                labels
            )
    
    def record_request_metrics(self, method: str, path: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        labels = {
            "method": method,
            "path": path,
            "status_code": str(status_code),
            "status_class": f"{status_code // 100}xx"
        }
        
        # Request count
        self.metrics.increment_counter("http_requests_total", labels)
        
        # Request duration
        self.metrics.record_histogram("http_request_duration_seconds", duration, labels)
        
        # Error rate
        if status_code >= 400:
            self.metrics.increment_counter("http_requests_errors_total", labels)
    
    def record_agent_metrics(self, agent_name: str, operation: str, 
                           success: bool, duration: float):
        """Record agent operation metrics."""
        labels = {
            "agent": agent_name,
            "operation": operation,
            "success": str(success).lower()
        }
        
        self.metrics.increment_counter("agent_operations_total", labels)
        self.metrics.record_histogram("agent_operation_duration_seconds", duration, labels)
        
        if not success:
            self.metrics.increment_counter("agent_operations_errors_total", labels)
    
    def record_database_metrics(self, operation: str, table: str, 
                              success: bool, duration: float):
        """Record database operation metrics."""
        labels = {
            "operation": operation,
            "table": table,
            "success": str(success).lower()
        }
        
        self.metrics.increment_counter("database_operations_total", labels)
        self.metrics.record_histogram("database_operation_duration_seconds", duration, labels)
        
        if not success:
            self.metrics.increment_counter("database_operations_errors_total", labels)
    
    def record_external_api_metrics(self, service: str, operation: str,
                                   status_code: int, duration: float):
        """Record external API call metrics."""
        labels = {
            "service": service,
            "operation": operation,
            "status_code": str(status_code),
            "success": str(status_code < 400).lower()
        }
        
        self.metrics.increment_counter("external_api_calls_total", labels)
        self.metrics.record_histogram("external_api_duration_seconds", duration, labels)
        
        if status_code >= 400:
            self.metrics.increment_counter("external_api_errors_total", labels)


class BusinessMetricsMonitor:
    """Monitor business-specific metrics."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.logger = get_logger("monitoring.business")
    
    def record_document_processing(self, document_type: str, success: bool, 
                                 duration: float, pages: int = 1):
        """Record document processing metrics."""
        labels = {
            "document_type": document_type,
            "success": str(success).lower()
        }
        
        self.metrics.increment_counter("documents_processed_total", labels)
        self.metrics.record_histogram("document_processing_duration_seconds", duration, labels)
        self.metrics.record_gauge("document_pages_processed", pages, labels)
        
        if not success:
            self.metrics.increment_counter("document_processing_errors_total", labels)
    
    def record_order_processing(self, order_type: str, line_items: int,
                              total_amount: float, success: bool):
        """Record order processing metrics."""
        labels = {
            "order_type": order_type,
            "success": str(success).lower()
        }
        
        self.metrics.increment_counter("orders_processed_total", labels)
        self.metrics.record_gauge("order_line_items", line_items, labels)
        self.metrics.record_gauge("order_total_amount", total_amount, labels)
        
        if not success:
            self.metrics.increment_counter("order_processing_errors_total", labels)
    
    def record_erp_integration(self, provider: str, operation: str,
                             success: bool, duration: float):
        """Record ERP integration metrics."""
        labels = {
            "provider": provider,
            "operation": operation,
            "success": str(success).lower()
        }
        
        self.metrics.increment_counter("erp_operations_total", labels)
        self.metrics.record_histogram("erp_operation_duration_seconds", duration, labels)
        
        if not success:
            self.metrics.increment_counter("erp_operations_errors_total", labels)
    
    def record_semantic_search(self, query_type: str, results_count: int,
                             confidence_score: float, duration: float):
        """Record semantic search metrics."""
        labels = {
            "query_type": query_type
        }
        
        self.metrics.increment_counter("semantic_searches_total", labels)
        self.metrics.record_histogram("semantic_search_duration_seconds", duration, labels)
        self.metrics.record_gauge("semantic_search_results_count", results_count, labels)
        self.metrics.record_gauge("semantic_search_confidence", confidence_score, labels)


class HealthMonitor:
    """Monitor application health and dependencies."""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.logger = get_logger("monitoring.health")
        self._health_checks = {}
        self._dependency_status = {}
    
    def register_health_check(self, name: str, check_func):
        """Register a health check function."""
        self._health_checks[name] = check_func
    
    async def check_health(self) -> Dict[str, Any]:
        """Run all health checks and return status."""
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "checks": {}
        }
        
        overall_healthy = True
        
        for name, check_func in self._health_checks.items():
            try:
                start_time = time.time()
                result = await check_func() if asyncio.iscoroutinefunction(check_func) else check_func()
                duration = time.time() - start_time
                
                is_healthy = result.get("healthy", True)
                health_status["checks"][name] = {
                    "healthy": is_healthy,
                    "duration_ms": round(duration * 1000, 2),
                    "details": result.get("details", {})
                }
                
                # Record metrics
                self.metrics.record_gauge(
                    f"health_check_status/{name}",
                    1 if is_healthy else 0
                )
                self.metrics.record_histogram(
                    f"health_check_duration_seconds/{name}",
                    duration
                )
                
                if not is_healthy:
                    overall_healthy = False
                    
            except Exception as e:
                self.logger.error(f"Health check {name} failed: {e}")
                health_status["checks"][name] = {
                    "healthy": False,
                    "error": str(e)
                }
                overall_healthy = False
                
                # Record error metric
                self.metrics.increment_counter(
                    "health_check_errors_total",
                    {"check": name}
                )
        
        health_status["status"] = "healthy" if overall_healthy else "unhealthy"
        
        # Record overall health
        self.metrics.record_gauge("application_health", 1 if overall_healthy else 0)
        
        return health_status
    
    def record_dependency_status(self, name: str, healthy: bool, response_time: float = None):
        """Record the status of an external dependency."""
        self._dependency_status[name] = {
            "healthy": healthy,
            "last_check": time.time(),
            "response_time": response_time
        }
        
        self.metrics.record_gauge(f"dependency_status/{name}", 1 if healthy else 0)
        if response_time is not None:
            self.metrics.record_histogram(f"dependency_response_time/{name}", response_time)


# Global instances
metrics_collector = MetricsCollector()
performance_monitor = PerformanceMonitor(metrics_collector)
business_metrics = BusinessMetricsMonitor(metrics_collector)
health_monitor = HealthMonitor(metrics_collector)


# Decorators for automatic metrics collection
def monitor_performance(operation_name: str = None):
    """Decorator to automatically monitor function performance."""
    def decorator(func):
        from functools import wraps
        import asyncio
        
        name = operation_name or f"{func.__module__}.{func.__name__}"
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with performance_monitor.timer(name):
                try:
                    result = await func(*args, **kwargs)
                    performance_monitor.metrics.increment_counter(
                        f"operation_success/{name}"
                    )
                    return result
                except Exception as e:
                    performance_monitor.metrics.increment_counter(
                        f"operation_error/{name}",
                        {"error_type": type(e).__name__}
                    )
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with performance_monitor.timer(name):
                try:
                    result = func(*args, **kwargs)
                    performance_monitor.metrics.increment_counter(
                        f"operation_success/{name}"
                    )
                    return result
                except Exception as e:
                    performance_monitor.metrics.increment_counter(
                        f"operation_error/{name}",
                        {"error_type": type(e).__name__}
                    )
                    raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator