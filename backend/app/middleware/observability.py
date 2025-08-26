"""
Observability middleware for automatic metrics collection
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from datetime import datetime
import time
import uuid

from ..evaluation.observability import observability

class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically collect observability metrics"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next):
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Record request start time
        start_time = time.time()
        
        # Extract request info
        method = request.method
        path = request.url.path
        user_id = self._extract_user_id(request)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Track metrics
            observability.track_api_request(
                endpoint=path,
                method=method,
                status_code=response.status_code,
                response_time=response_time,
                user_id=user_id
            )
            
            # Add response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            
            return response
            
        except Exception as e:
            # Calculate response time for errors
            response_time = time.time() - start_time
            
            # Track error
            observability.track_api_request(
                endpoint=path,
                method=method,
                status_code=500,
                response_time=response_time,
                user_id=user_id
            )
            
            # Re-raise the exception
            raise e
    
    def _extract_user_id(self, request: Request) -> str:
        """Extract user ID from request (if available)"""
        # Try to get user ID from JWT token or session
        # For now, return None - would implement based on auth system
        return None

class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for performance monitoring"""
    
    def __init__(self, app: ASGIApp, slow_request_threshold: float = 2.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        response_time = time.time() - start_time
        
        # Log slow requests
        if response_time > self.slow_request_threshold:
            print(f"SLOW REQUEST: {request.method} {request.url.path} took {response_time:.3f}s")
        
        return response