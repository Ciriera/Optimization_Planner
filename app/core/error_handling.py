"""
Comprehensive error handling and exception management.
"""
import traceback
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError

from app.monitoring.logger import get_logger, log_security_event

logger = get_logger(__name__)


class OptimizationPlannerException(Exception):
    """Base exception for Optimization Planner."""
    
    def __init__(self, message: str, error_code: str = "GENERIC_ERROR", details: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(OptimizationPlannerException):
    """Validation error exception."""
    
    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message, "VALIDATION_ERROR", details)
        self.field = field


class BusinessLogicException(OptimizationPlannerException):
    """Business logic error exception."""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, "BUSINESS_LOGIC_ERROR", details)


class AlgorithmException(OptimizationPlannerException):
    """Algorithm execution error exception."""
    
    def __init__(self, message: str, algorithm_type: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message, "ALGORITHM_ERROR", details)
        self.algorithm_type = algorithm_type


class DatabaseException(OptimizationPlannerException):
    """Database operation error exception."""
    
    def __init__(self, message: str, details: Optional[Dict] = None):
        super().__init__(message, "DATABASE_ERROR", details)


class AuthorizationException(OptimizationPlannerException):
    """Authorization error exception."""
    
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict] = None):
        super().__init__(message, "AUTHORIZATION_ERROR", details)


class ResourceNotFoundException(OptimizationPlannerException):
    """Resource not found error exception."""
    
    def __init__(self, resource_type: str, resource_id: Any, details: Optional[Dict] = None):
        message = f"{resource_type} with ID {resource_id} not found"
        super().__init__(message, "RESOURCE_NOT_FOUND", details)
        self.resource_type = resource_type
        self.resource_id = resource_id


class RateLimitException(OptimizationPlannerException):
    """Rate limit exceeded error exception."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60, details: Optional[Dict] = None):
        super().__init__(message, "RATE_LIMIT_EXCEEDED", details)
        self.retry_after = retry_after


def create_error_response(
    message: str,
    error_code: str = "GENERIC_ERROR",
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    details: Optional[Dict] = None
) -> JSONResponse:
    """Create standardized error response."""
    
    error_response = {
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": "2024-01-01T00:00:00Z"  # Will be replaced with actual timestamp
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=error_response
    )


async def optimization_planner_exception_handler(
    request: Request, 
    exc: OptimizationPlannerException
) -> JSONResponse:
    """Handle OptimizationPlannerException."""
    
    logger.error(f"OptimizationPlannerException: {exc.message}", extra={
        "error_code": exc.error_code,
        "details": exc.details,
        "path": str(request.url),
        "method": request.method
    })
    
    # Determine status code based on error type
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    if isinstance(exc, ValidationException):
        status_code = status.HTTP_400_BAD_REQUEST
    elif isinstance(exc, BusinessLogicException):
        status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    elif isinstance(exc, AlgorithmException):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(exc, DatabaseException):
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    elif isinstance(exc, AuthorizationException):
        status_code = status.HTTP_403_FORBIDDEN
    elif isinstance(exc, ResourceNotFoundException):
        status_code = status.HTTP_404_NOT_FOUND
    elif isinstance(exc, RateLimitException):
        status_code = status.HTTP_429_TOO_MANY_REQUESTS
    
    return create_error_response(
        message=exc.message,
        error_code=exc.error_code,
        status_code=status_code,
        details=exc.details
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTPException."""
    
    # HER ZAMAN log yaz - stderr'e de yaz
    import sys
    error_msg = f"""
{'='*80}
[HTTP EXCEPTION HANDLER]
Status Code: {exc.status_code}
Detail: {exc.detail}
Path: {request.url.path}
Method: {request.method}
{'='*80}
"""
    print(error_msg, flush=True)
    print(error_msg, file=sys.stderr, flush=True)
    
    logger.warning(f"HTTPException: {exc.detail}", extra={
        "status_code": exc.status_code,
        "path": str(request.url),
        "method": request.method
    })
    
    return create_error_response(
        message=exc.detail,
        error_code=f"HTTP_{exc.status_code}",
        status_code=exc.status_code
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(f"Validation error: {errors}", extra={
        "path": str(request.url),
        "method": request.method
    })
    
    return create_error_response(
        message="Validation failed",
        error_code="VALIDATION_ERROR",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details={"errors": errors}
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy exceptions."""
    
    logger.error(f"Database error: {str(exc)}", extra={
        "path": str(request.url),
        "method": request.method,
        "exception_type": type(exc).__name__
    })
    
    # Log security event for potential SQL injection attempts
    if "sql" in str(exc).lower() or "injection" in str(exc).lower():
        log_security_event(
            event_type="potential_sql_injection",
            ip_address=request.client.host,
            details={"exception": str(exc)}
        )
    
    if isinstance(exc, IntegrityError):
        return create_error_response(
            message="Database integrity constraint violated",
            error_code="INTEGRITY_ERROR",
            status_code=status.HTTP_409_CONFLICT
        )
    
    return create_error_response(
        message="Database operation failed",
        error_code="DATABASE_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle generic exceptions."""
    
    import sys
    import traceback
    
    # HER ZAMAN log yaz - stderr'e de yaz
    error_traceback = traceback.format_exc()
    error_msg = f"""
{'='*80}
[GENERIC EXCEPTION HANDLER]
Exception Type: {type(exc).__name__}
Exception Message: {str(exc)}
Path: {request.url.path}
Method: {request.method}
Traceback:
{error_traceback}
{'='*80}
"""
    print(error_msg, flush=True)
    print(error_msg, file=sys.stderr, flush=True)
    
    logger.error(f"Unexpected error: {str(exc)}", extra={
        "path": str(request.url),
        "method": request.method,
        "exception_type": type(exc).__name__,
        "traceback": error_traceback
    })
    
    # Log security event for unexpected errors
    log_security_event(
        event_type="unexpected_error",
        ip_address=request.client.host,
        details={
            "exception": str(exc),
            "exception_type": type(exc).__name__
        }
    )
    
    return create_error_response(
        message="An unexpected error occurred",
        error_code="INTERNAL_SERVER_ERROR",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """Validate that required fields are present."""
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing_fields:
        raise ValidationException(
            message=f"Missing required fields: {', '.join(missing_fields)}",
            details={"missing_fields": missing_fields}
        )


def validate_field_types(data: Dict[str, Any], field_types: Dict[str, type]) -> None:
    """Validate field types."""
    errors = []
    
    for field, expected_type in field_types.items():
        if field in data and data[field] is not None:
            if not isinstance(data[field], expected_type):
                errors.append({
                    "field": field,
                    "expected_type": expected_type.__name__,
                    "actual_type": type(data[field]).__name__
                })
    
    if errors:
        raise ValidationException(
            message="Field type validation failed",
            details={"type_errors": errors}
        )


def validate_business_rules(data: Dict[str, Any], rules: Dict[str, callable]) -> None:
    """Validate business rules."""
    errors = []
    
    for field, rule_func in rules.items():
        if field in data:
            try:
                if not rule_func(data[field]):
                    errors.append({
                        "field": field,
                        "message": f"Business rule validation failed for {field}"
                    })
            except Exception as e:
                errors.append({
                    "field": field,
                    "message": f"Rule validation error: {str(e)}"
                })
    
    if errors:
        raise BusinessLogicException(
            message="Business rule validation failed",
            details={"rule_errors": errors}
        )


class ErrorContext:
    """Context manager for error handling with additional context."""
    
    def __init__(self, operation: str, **context):
        self.operation = operation
        self.context = context
        self.logger = get_logger(__name__)
    
    def __enter__(self):
        self.logger.info(f"Starting operation: {self.operation}", extra=self.context)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.logger.error(
                f"Operation failed: {self.operation}",
                extra={
                    **self.context,
                    "exception": str(exc_val),
                    "exception_type": exc_type.__name__
                }
            )
        else:
            self.logger.info(f"Operation completed: {self.operation}", extra=self.context)
        
        return False  # Don't suppress exceptions
