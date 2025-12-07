from typing import Callable, Dict, Any
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import time
from starlette.middleware.base import BaseHTTPMiddleware
import json
import traceback

from app.core.config import settings
from app.security.rate_limiter import rate_limiter, check_rate_limit
from app.monitoring.logger import get_logger, RequestTimer
from app.core.error_handling import create_error_response


class APIResponseMiddleware(BaseHTTPMiddleware):
    """
    Middleware for standardizing API responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip middleware for non-API routes
        if not request.url.path.startswith("/api"):
            return await call_next(request)
        
        # HER ZAMAN log yaz - APIResponseMiddleware başlangıcı
        print(f"[API RESPONSE MIDDLEWARE] {request.method} {request.url.path}")
        
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
        # Skip ALL processing for /api/v1/process to prevent terminal spam
        # ProcessEndpointBlockerMiddleware handles it, but we skip logging here
        if request.url.path == "/api/v1/process":
            # Let ProcessEndpointBlockerMiddleware handle it, just skip logging
            return await call_next(request)
        
        # Generate a unique request ID
        request_id = id(request)
        
        start_time = time.time()
        
        # Log the request - HER ZAMAN log yaz (DEBUG kontrolü kaldırıldı)
        print(f"[REQUEST] {request.method} {request.url.path} (ID: {request_id})")
        if request.url.query:
            print(f"         Query params: {request.url.query}")
        
        # Process the request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            print(f"[REQUEST ERROR] {request.method} {request.url.path} - {type(e).__name__}: {str(e)}")
            raise
        
        # Calculate the request processing time
        process_time = time.time() - start_time
        
        # Log the response time
        print(f"[REQUEST] {request.method} {request.url.path} - {response.status_code} ({process_time:.4f}s)")
        
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
    
    def __init__(self, app: FastAPI, rate_limit: int = 1000, time_window: int = 60):
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


class ProcessEndpointBlockerMiddleware(BaseHTTPMiddleware):
    """
    Middleware to silently block all requests to /api/v1/process endpoint before any other processing.
    This runs FIRST (added last, so executes first in the middleware chain).
    Returns 204 No Content (instead of 404) to minimize browser retries and completely suppresses logging.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Silently block ALL requests to non-existent /api/v1/process endpoint
        # Use 204 No Content to tell browser: "Nothing to see here, stop asking"
        if request.url.path == "/api/v1/process":
            # 204 No Content - tells browser to stop retrying
            # CORS headers still included for preflight
            from starlette.responses import Response
            return Response(
                status_code=204,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                    "Access-Control-Allow-Headers": "*",
                    "Access-Control-Max-Age": "86400",  # Cache for 24 hours
                    "Cache-Control": "public, max-age=86400",  # Tell browser to cache this response
                },
                background=None  # Prevent any background tasks
            )
        
        return await call_next(request)


def setup_middleware(app: FastAPI) -> None:
    """
    Setup middleware for the application.
    IMPORTANT: Middleware order matters! Last added = first executed.
    """
    # Add CORS middleware first (will be executed last)
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add other middleware
    app.add_middleware(APIResponseMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ExceptionMiddleware)
    app.add_middleware(RateLimiterMiddleware, rate_limit=1000, time_window=60)
    
    # Add ProcessEndpointBlockerMiddleware LAST so it executes FIRST
    app.add_middleware(ProcessEndpointBlockerMiddleware) 