"""
Performance Monitoring Middleware

Tracks request performance metrics and logs slow requests.
"""

import time
import logging
import uuid
from typing import Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

logger = logging.getLogger(__name__)

class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to track request performance and log metrics"""
    
    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold  # seconds
    
    async def dispatch(self, request: Request, call_next):
        # Generate correlation ID if not present
        correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        
        # Record start time
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add performance headers
        response.headers["X-Process-Time"] = str(round(process_time, 4))
        response.headers["X-Correlation-ID"] = correlation_id
        
        # Log performance metrics
        self._log_request_metrics(
            request, 
            response, 
            process_time, 
            correlation_id
        )
        
        return response
    
    def _log_request_metrics(
        self, 
        request: Request, 
        response: Response, 
        process_time: float, 
        correlation_id: str
    ):
        """Log request performance metrics"""
        
        # Prepare log data
        log_data = {
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "process_time": round(process_time, 4),
            "user_agent": request.headers.get("user-agent", ""),
            "client_ip": self._get_client_ip(request)
        }
        
        # Add query parameters if present (but sanitize sensitive data)
        if request.url.query:
            query_params = dict(request.query_params)
            # Remove sensitive parameters
            sensitive_params = ['password', 'token', 'key', 'secret']
            for param in sensitive_params:
                if param in query_params:
                    query_params[param] = "[REDACTED]"
            log_data["query_params"] = query_params
        
        # Log based on performance and status
        if process_time > self.slow_request_threshold:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {process_time:.4f}s",
                extra=log_data
            )
        elif response.status_code >= 400:
            logger.warning(
                f"Error response: {request.method} {request.url.path} "
                f"returned {response.status_code}",
                extra=log_data
            )
        else:
            logger.info(
                f"Request: {request.method} {request.url.path} "
                f"({process_time:.4f}s)",
                extra=log_data
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        
        # Check for forwarded headers (common in load balancers/proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"

class RequestSizeMiddleware(BaseHTTPMiddleware):
    """Middleware to track and limit request sizes"""
    
    def __init__(self, app, max_request_size: int = 50 * 1024 * 1024):  # 50MB default
        super().__init__(app)
        self.max_request_size = max_request_size
    
    async def dispatch(self, request: Request, call_next):
        # Check content length
        content_length = request.headers.get("content-length")
        if content_length:
            content_length = int(content_length)
            if content_length > self.max_request_size:
                logger.warning(
                    f"Request too large: {content_length} bytes "
                    f"(max: {self.max_request_size})",
                    extra={
                        "correlation_id": getattr(request.state, 'correlation_id', 'unknown'),
                        "method": request.method,
                        "path": request.url.path,
                        "content_length": content_length
                    }
                )
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "Request entity too large",
                        "max_size": self.max_request_size,
                        "received_size": content_length
                    }
                )
        
        response = await call_next(request)
        
        # Log request size for monitoring
        if content_length and content_length > 1024 * 1024:  # Log requests > 1MB
            logger.info(
                f"Large request processed: {content_length} bytes",
                extra={
                    "correlation_id": getattr(request.state, 'correlation_id', 'unknown'),
                    "method": request.method,
                    "path": request.url.path,
                    "content_length": content_length
                }
            )
        
        return response

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: Dict[str, Dict[str, Any]] = {}
        self.window_size = 60  # 1 minute window
    
    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Clean old entries
        self._cleanup_old_entries(current_time)
        
        # Check rate limit
        if self._is_rate_limited(client_ip, current_time):
            logger.warning(
                f"Rate limit exceeded for IP: {client_ip}",
                extra={
                    "correlation_id": getattr(request.state, 'correlation_id', 'unknown'),
                    "client_ip": client_ip,
                    "method": request.method,
                    "path": request.url.path
                }
            )
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "limit": self.requests_per_minute,
                    "window": "1 minute"
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0"
                }
            )
        
        # Record request
        self._record_request(client_ip, current_time)
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self._get_remaining_requests(client_ip, current_time)
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        if hasattr(request, "client") and request.client:
            return request.client.host
        
        return "unknown"
    
    def _cleanup_old_entries(self, current_time: float):
        """Remove entries older than the window size"""
        cutoff_time = current_time - self.window_size
        
        for ip in list(self.request_counts.keys()):
            self.request_counts[ip]["requests"] = [
                req_time for req_time in self.request_counts[ip]["requests"]
                if req_time > cutoff_time
            ]
            
            # Remove IP if no recent requests
            if not self.request_counts[ip]["requests"]:
                del self.request_counts[ip]
    
    def _is_rate_limited(self, client_ip: str, current_time: float) -> bool:
        """Check if client IP is rate limited"""
        if client_ip not in self.request_counts:
            return False
        
        recent_requests = len(self.request_counts[client_ip]["requests"])
        return recent_requests >= self.requests_per_minute
    
    def _record_request(self, client_ip: str, current_time: float):
        """Record a request for the client IP"""
        if client_ip not in self.request_counts:
            self.request_counts[client_ip] = {"requests": []}
        
        self.request_counts[client_ip]["requests"].append(current_time)
    
    def _get_remaining_requests(self, client_ip: str, current_time: float) -> int:
        """Get remaining requests for the client IP"""
        if client_ip not in self.request_counts:
            return self.requests_per_minute
        
        recent_requests = len(self.request_counts[client_ip]["requests"])
        return max(0, self.requests_per_minute - recent_requests)