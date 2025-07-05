from typing import Callable, Dict, Any
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import time
from starlette.middleware.base import BaseHTTPMiddleware
import json
import traceback

from app.core.config import settings


class APIResponseMiddleware(BaseHTTPMiddleware):
    """
    Middleware for standardizing API responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip middleware for non-API routes
        if not request.url.path.startswith("/api"):
            return await call_next(request)
        
        start_time = time.time()
        
        try:
            # Process the request and get the response
            response = await call_next(request)
            
            # If response is not a JSON response, return it as is
            if not isinstance(response, JSONResponse):
                return response
            
            # Get the response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Parse the response body
            response_json = json.loads(response_body)
            
            # Create a standardized response
            standardized_response = {
                "status": "success",
                "data": response_json,
                "message": None
            }
            
            # Return the standardized response
            return JSONResponse(
                content=standardized_response,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )
        except Exception as e:
            # Handle and log errors
            process_time = time.time() - start_time
            error_detail = f"Error processing request: {str(e)}"
            
            # In debug mode, include traceback
            debug = getattr(settings, "DEBUG", False)
            if debug:
                error_detail += f"\n{traceback.format_exc()}"
                
            print(f"Error: {error_detail}")
            print(f"Request took {process_time:.4f} seconds to process")
            
            # Return error response
            return JSONResponse(
                content={
                    "status": "error",
                    "data": None,
                    "message": str(e)
                },
                status_code=500
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging request details.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate a unique request ID
        request_id = id(request)
        
        start_time = time.time()
        
        # Log the request
        debug = getattr(settings, "DEBUG", False)
        if debug:
            print(f"Request {request_id}: {request.method} {request.url.path}")
        
        # Process the request
        response = await call_next(request)
        
        # Calculate the request processing time
        process_time = time.time() - start_time
        
        # Log the response time
        if debug:
            print(f"Request {request_id} took {process_time:.4f} seconds to process")
        
        return response


class ExceptionMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling exceptions.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            # Process the request
            response = await call_next(request)
            return response
        except Exception as e:
            # Log the error
            error_detail = f"Exception: {str(e)}"
            debug = getattr(settings, "DEBUG", False)
            if debug:
                error_detail += f"\n{traceback.format_exc()}"
            print(error_detail)
            
            # Return an error response
            return JSONResponse(
                content={
                    "status": "error",
                    "data": None,
                    "message": str(e)
                },
                status_code=500
            )


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    API istek sınırlaması yapar.
    """
    
    def __init__(self, app: FastAPI, rate_limit: int = 20, time_window: int = 60):
        super().__init__(app)
        self.rate_limit = rate_limit  # İstek sayısı
        self.time_window = time_window  # Saniye
        self.requests = {}  # {ip: [(timestamp, path), ...]}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # İstemci IP'sini al
        client_ip = request.client.host if request.client else "unknown"
        
        # Şu anki zamanı al
        current_time = time.time()
        
        # İstemcinin isteklerini al
        client_requests = self.requests.get(client_ip, [])
        
        # Eski istekleri temizle
        client_requests = [r for r in client_requests if current_time - r[0] < self.time_window]
        
        # İstek sayısını kontrol et
        if len(client_requests) >= self.rate_limit:
            # İstek sınırı aşıldı
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "data": None,
                    "message": "İstek sınırı aşıldı. Lütfen daha sonra tekrar deneyin.",
                    "error_code": "RATE_LIMIT_EXCEEDED"
                }
            )
        
        # Yeni isteği ekle
        client_requests.append((current_time, request.url.path))
        self.requests[client_ip] = client_requests
        
        # İsteği işle
        return await call_next(request)


def setup_middleware(app: FastAPI) -> None:
    """
    Setup middleware for the application.
    """
    app.add_middleware(APIResponseMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ExceptionMiddleware)
    app.add_middleware(RateLimiterMiddleware, rate_limit=20, time_window=60) 