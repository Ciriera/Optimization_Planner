"""
Input validation and sanitization utilities.
"""
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, validator
from fastapi import HTTPException, status


class SQLInjectionValidator:
    """SQL injection prevention utilities."""
    
    # Common SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+['\"].*['\"])",
        r"(\bUNION\s+SELECT\b)",
        r"(\bDROP\s+TABLE\b)",
        r"(\bINSERT\s+INTO\b)",
        r"(\bDELETE\s+FROM\b)",
        r"(\bUPDATE\s+SET\b)",
        r"(--|\#|\/\*|\*\/)",
        r"(\bxp_\w+\b)",
        r"(\bsp_\w+\b)",
    ]
    
    @classmethod
    def is_safe_string(cls, text: str) -> bool:
        """Check if string is safe from SQL injection."""
        if not isinstance(text, str):
            return True
        
        text_upper = text.upper()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return False
        return True
    
    @classmethod
    def sanitize_string(cls, text: str) -> str:
        """Sanitize string to prevent SQL injection."""
        if not isinstance(text, str):
            return str(text)
        
        # Remove potentially dangerous characters
        dangerous_chars = [';', '--', '/*', '*/', '\x00', '\r', '\n']
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        return text.strip()


class XSSValidator:
    """XSS prevention utilities."""
    
    # Common XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
        r"<link[^>]*>",
        r"<meta[^>]*>",
        r"<style[^>]*>.*?</style>",
        r"expression\s*\(",
        r"url\s*\(",
    ]
    
    @classmethod
    def is_safe_html(cls, text: str) -> bool:
        """Check if HTML is safe from XSS."""
        if not isinstance(text, str):
            return True
        
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE | re.DOTALL):
                return False
        return True
    
    @classmethod
    def sanitize_html(cls, text: str) -> str:
        """Sanitize HTML to prevent XSS."""
        if not isinstance(text, str):
            return str(text)
        
        # Remove script tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove javascript: protocols
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        
        # Remove event handlers
        text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
        
        return text.strip()


class InputValidator:
    """Comprehensive input validation."""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Validate phone number format."""
        pattern = r'^[\+]?[1-9][\d]{0,15}$'
        return bool(re.match(pattern, phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')))
    
    @staticmethod
    def validate_student_number(student_number: str) -> bool:
        """Validate student number format."""
        pattern = r'^\d{8,10}$'
        return bool(re.match(pattern, student_number))
    
    @staticmethod
    def validate_classroom_name(name: str) -> bool:
        """Validate classroom name format."""
        pattern = r'^[A-Z]\d{3}$'
        return bool(re.match(pattern, name))
    
    @staticmethod
    def validate_project_title(title: str) -> bool:
        """Validate project title."""
        if not title or len(title.strip()) < 3:
            return False
        if len(title) > 200:
            return False
        return SQLInjectionValidator.is_safe_string(title) and XSSValidator.is_safe_html(title)
    
    @staticmethod
    def validate_instructor_name(name: str) -> bool:
        """Validate instructor name."""
        if not name or len(name.strip()) < 2:
            return False
        if len(name) > 100:
            return False
        return SQLInjectionValidator.is_safe_string(name) and XSSValidator.is_safe_html(name)


class SecureInputModel(BaseModel):
    """Base model with security validators."""
    
    @validator('*', pre=True)
    def validate_all_fields(cls, v):
        """Validate all fields for security."""
        if isinstance(v, str):
            # Check for SQL injection
            if not SQLInjectionValidator.is_safe_string(v):
                raise ValueError("Potentially unsafe input detected")
            
            # Check for XSS
            if not XSSValidator.is_safe_html(v):
                raise ValueError("Potentially unsafe HTML detected")
        
        return v


def validate_request_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize request data."""
    validated_data = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            # Sanitize string values
            validated_data[key] = SQLInjectionValidator.sanitize_string(
                XSSValidator.sanitize_html(value)
            )
        else:
            validated_data[key] = value
    
    return validated_data


def validate_file_upload(filename: str, content_type: str, max_size: int = 10 * 1024 * 1024) -> None:
    """Validate file upload."""
    # Check file extension
    allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.csv', '.txt']
    file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
    
    if f'.{file_ext}' not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type .{file_ext} not allowed"
        )
    
    # Check content type
    allowed_types = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/csv',
        'text/plain'
    ]
    
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Content type {content_type} not allowed"
        )
    
    # Check filename for malicious patterns
    if not SQLInjectionValidator.is_safe_string(filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )
