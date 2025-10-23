"""
Comprehensive logging and monitoring system.
"""
import logging
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import sys

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record):
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        if hasattr(record, 'duration'):
            log_entry["duration"] = record.duration
        if hasattr(record, 'status_code'):
            log_entry["status_code"] = record.status_code
        
        return json.dumps(log_entry, ensure_ascii=False)


class StructuredLogger:
    """Structured logging system."""
    
    def __init__(self):
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration."""
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Root logger configuration
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler for all logs
        file_handler = logging.FileHandler(log_dir / "app.log")
        file_handler.setLevel(logging.INFO)
        file_formatter = JSONFormatter()
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Error file handler
        error_handler = logging.FileHandler(log_dir / "errors.log")
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        root_logger.addHandler(error_handler)
        
        # Security file handler
        security_handler = logging.FileHandler(log_dir / "security.log")
        security_handler.setLevel(logging.WARNING)
        security_handler.setFormatter(file_formatter)
        security_logger = logging.getLogger("security")
        security_logger.addHandler(security_handler)
        security_logger.setLevel(logging.WARNING)
        security_logger.propagate = False
        
        # Performance file handler
        performance_handler = logging.FileHandler(log_dir / "performance.log")
        performance_handler.setLevel(logging.INFO)
        performance_handler.setFormatter(file_formatter)
        performance_logger = logging.getLogger("performance")
        performance_logger.addHandler(performance_handler)
        performance_logger.setLevel(logging.INFO)
        performance_logger.propagate = False


class MetricsCollector:
    """Metrics collection system."""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = {
            "requests_total": 0,
            "requests_by_status": {},
            "requests_by_endpoint": {},
            "response_times": [],
            "error_count": 0,
            "active_users": set(),
            "algorithms_run": {},
            "optimization_results": [],
        }
    
    def increment_request_count(self, endpoint: str, status_code: int):
        """Increment request count metrics."""
        self.metrics["requests_total"] += 1
        
        # By status code
        status_key = str(status_code)
        self.metrics["requests_by_status"][status_key] = \
            self.metrics["requests_by_status"].get(status_key, 0) + 1
        
        # By endpoint
        self.metrics["requests_by_endpoint"][endpoint] = \
            self.metrics["requests_by_endpoint"].get(endpoint, 0) + 1
        
        # Error count
        if status_code >= 400:
            self.metrics["error_count"] += 1
    
    def record_response_time(self, duration: float):
        """Record response time."""
        self.metrics["response_times"].append(duration)
        # Keep only last 1000 response times
        if len(self.metrics["response_times"]) > 1000:
            self.metrics["response_times"] = self.metrics["response_times"][-1000:]
    
    def record_algorithm_run(self, algorithm_type: str, success: bool, duration: float):
        """Record algorithm execution."""
        if algorithm_type not in self.metrics["algorithms_run"]:
            self.metrics["algorithms_run"][algorithm_type] = {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "avg_duration": 0,
                "durations": []
            }
        
        algo_metrics = self.metrics["algorithms_run"][algorithm_type]
        algo_metrics["total"] += 1
        algo_metrics["durations"].append(duration)
        
        if success:
            algo_metrics["successful"] += 1
        else:
            algo_metrics["failed"] += 1
        
        # Calculate average duration
        algo_metrics["avg_duration"] = sum(algo_metrics["durations"]) / len(algo_metrics["durations"])
        
        # Keep only last 100 durations
        if len(algo_metrics["durations"]) > 100:
            algo_metrics["durations"] = algo_metrics["durations"][-100:]
    
    def record_optimization_result(self, algorithm_type: str, fitness_score: float, duration: float):
        """Record optimization result."""
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "algorithm": algorithm_type,
            "fitness_score": fitness_score,
            "duration": duration
        }
        self.metrics["optimization_results"].append(result)
        
        # Keep only last 1000 results
        if len(self.metrics["optimization_results"]) > 1000:
            self.metrics["optimization_results"] = self.metrics["optimization_results"][-1000:]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        response_times = self.metrics["response_times"]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            "requests_total": self.metrics["requests_total"],
            "requests_by_status": self.metrics["requests_by_status"],
            "requests_by_endpoint": self.metrics["requests_by_endpoint"],
            "avg_response_time": avg_response_time,
            "error_count": self.metrics["error_count"],
            "error_rate": self.metrics["error_count"] / max(1, self.metrics["requests_total"]),
            "active_users_count": len(self.metrics["active_users"]),
            "algorithms_run": self.metrics["algorithms_run"],
            "recent_optimizations": self.metrics["optimization_results"][-10:],
        }


# Global instances
structured_logger = StructuredLogger()
metrics_collector = MetricsCollector()


def get_logger(name: str) -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)


def log_security_event(event_type: str, user_id: Optional[str] = None, 
                      ip_address: Optional[str] = None, details: Optional[Dict] = None):
    """Log security events."""
    security_logger = logging.getLogger("security")
    
    log_data = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if user_id:
        log_data["user_id"] = user_id
    if ip_address:
        log_data["ip_address"] = ip_address
    if details:
        log_data.update(details)
    
    security_logger.warning(json.dumps(log_data, ensure_ascii=False))


def log_performance_metric(operation: str, duration: float, details: Optional[Dict] = None):
    """Log performance metrics."""
    performance_logger = logging.getLogger("performance")
    
    log_data = {
        "operation": operation,
        "duration": duration,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if details:
        log_data.update(details)
    
    performance_logger.info(json.dumps(log_data, ensure_ascii=False))


class RequestTimer:
    """Context manager for timing requests."""
    
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            log_performance_metric(f"request_{self.endpoint}", duration)
            metrics_collector.record_response_time(duration)
