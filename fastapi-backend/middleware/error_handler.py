"""
Error Handler Middleware

Comprehensive error handling for the FastAPI backend with proper logging
and structured error responses.
"""

import logging
import traceback
import uuid
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import ValidationError
import asyncpg
try:
    from qdrant_client.http.exceptions import QdrantException
except ImportError:
    # Fallback for different qdrant-client versions
    QdrantException = Exception
import httpx

from utils.logging import log_service_call, log_service_result

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Middleware to handle all exceptions and provide consistent error responses"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate correlation ID if not present
        correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        
        try:
            response = await call_next(request)
            return response
            
        except Exception as exc:
            return await self.handle_exception(request, exc, correlation_id)
    
    async def handle_exception(
        self, 
        request: Request, 
        exc: Exception, 
        correlation_id: str
    ) -> JSONResponse:
        """Handle different types of exceptions and return appropriate responses"""
        
        # Log the exception with context
        logger.error(
            f"Exception in {request.method} {request.url.path}: {str(exc)}",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "exception_type": type(exc).__name__,
                "traceback": traceback.format_exc()
            },
            exc_info=True
        )
        
        # Handle specific exception types
        if isinstance(exc, HTTPException):
            return await self._handle_http_exception(exc, correlation_id)
        elif isinstance(exc, StarletteHTTPException):
            return await self._handle_starlette_http_exception(exc, correlation_id)
        elif isinstance(exc, RequestValidationError):
            return await self._handle_validation_error(exc, correlation_id)
        elif isinstance(exc, ValidationError):
            return await self._handle_pydantic_validation_error(exc, correlation_id)
        elif isinstance(exc, asyncpg.PostgresError):
            return await self._handle_database_error(exc, correlation_id)
        elif isinstance(exc, QdrantException):
            return await self._handle_qdrant_error(exc, correlation_id)
        elif isinstance(exc, httpx.HTTPError):
            return await self._handle_http_client_error(exc, correlation_id)
        else:
            return await self._handle_generic_error(exc, correlation_id)
    
    async def _handle_http_exception(
        self, 
        exc: HTTPException, 
        correlation_id: str
    ) -> JSONResponse:
        """Handle FastAPI HTTPException"""
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "correlation_id": correlation_id,
                "type": "http_exception"
            }
        )
    
    async def _handle_starlette_http_exception(
        self, 
        exc: StarletteHTTPException, 
        correlation_id: str
    ) -> JSONResponse:
        """Handle Starlette HTTPException"""
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "correlation_id": correlation_id,
                "type": "http_exception"
            }
        )
    
    async def _handle_validation_error(
        self, 
        exc: RequestValidationError, 
        correlation_id: str
    ) -> JSONResponse:
        """Handle request validation errors"""
        
        errors = []
        for error in exc.errors():
            errors.append({
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "details": errors,
                "status_code": 422,
                "correlation_id": correlation_id,
                "type": "validation_error"
            }
        )
    
    async def _handle_pydantic_validation_error(
        self, 
        exc: ValidationError, 
        correlation_id: str
    ) -> JSONResponse:
        """Handle Pydantic validation errors"""
        
        errors = []
        for error in exc.errors():
            errors.append({
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Data validation error",
                "details": errors,
                "status_code": 422,
                "correlation_id": correlation_id,
                "type": "pydantic_validation_error"
            }
        )
    
    async def _handle_database_error(
        self, 
        exc: asyncpg.PostgresError, 
        correlation_id: str
    ) -> JSONResponse:
        """Handle PostgreSQL database errors"""
        
        # Don't expose internal database details in production
        error_message = "Database operation failed"
        
        # Log detailed error for debugging
        logger.error(
            f"Database error: {exc}",
            extra={
                "correlation_id": correlation_id,
                "sqlstate": getattr(exc, 'sqlstate', None),
                "detail": getattr(exc, 'detail', None),
                "hint": getattr(exc, 'hint', None)
            }
        )
        
        # Provide more specific error messages for common cases
        if hasattr(exc, 'sqlstate'):
            if exc.sqlstate == '23505':  # unique_violation
                error_message = "A record with this information already exists"
            elif exc.sqlstate == '23503':  # foreign_key_violation
                error_message = "Referenced record does not exist"
            elif exc.sqlstate == '23502':  # not_null_violation
                error_message = "Required field is missing"
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": error_message,
                "status_code": 500,
                "correlation_id": correlation_id,
                "type": "database_error"
            }
        )
    
    async def _handle_qdrant_error(
        self, 
        exc: QdrantException, 
        correlation_id: str
    ) -> JSONResponse:
        """Handle Qdrant vector database errors"""
        
        logger.error(
            f"Qdrant error: {exc}",
            extra={"correlation_id": correlation_id}
        )
        
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "Vector database service unavailable",
                "status_code": 503,
                "correlation_id": correlation_id,
                "type": "qdrant_error"
            }
        )
    
    async def _handle_http_client_error(
        self, 
        exc: httpx.HTTPError, 
        correlation_id: str
    ) -> JSONResponse:
        """Handle HTTP client errors (external service calls)"""
        
        logger.error(
            f"HTTP client error: {exc}",
            extra={"correlation_id": correlation_id}
        )
        
        error_message = "External service unavailable"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
        if isinstance(exc, httpx.TimeoutException):
            error_message = "External service timeout"
        elif isinstance(exc, httpx.ConnectError):
            error_message = "Unable to connect to external service"
        
        return JSONResponse(
            status_code=status_code,
            content={
                "error": error_message,
                "status_code": status_code,
                "correlation_id": correlation_id,
                "type": "http_client_error"
            }
        )
    
    async def _handle_generic_error(
        self, 
        exc: Exception, 
        correlation_id: str
    ) -> JSONResponse:
        """Handle any other unexpected errors"""
        
        logger.error(
            f"Unexpected error: {exc}",
            extra={
                "correlation_id": correlation_id,
                "exception_type": type(exc).__name__
            },
            exc_info=True
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "An unexpected error occurred",
                "status_code": 500,
                "correlation_id": correlation_id,
                "type": "internal_server_error"
            }
        )

# Custom exception classes for specific business logic errors

class BusinessLogicError(Exception):
    """Base class for business logic errors"""
    
    def __init__(self, message: str, status_code: int = 400, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(message)

class AuthenticationError(BusinessLogicError):
    """Authentication related errors"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, "AUTHENTICATION_ERROR")

class AuthorizationError(BusinessLogicError):
    """Authorization related errors"""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status.HTTP_403_FORBIDDEN, "AUTHORIZATION_ERROR")

class ResourceNotFoundError(BusinessLogicError):
    """Resource not found errors"""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND, "RESOURCE_NOT_FOUND")

class ConflictError(BusinessLogicError):
    """Resource conflict errors"""
    
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status.HTTP_409_CONFLICT, "RESOURCE_CONFLICT")

class ServiceUnavailableError(BusinessLogicError):
    """External service unavailable errors"""
    
    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(message, status.HTTP_503_SERVICE_UNAVAILABLE, "SERVICE_UNAVAILABLE")

class RateLimitError(BusinessLogicError):
    """Rate limiting errors"""
    
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS, "RATE_LIMIT_EXCEEDED")

# Exception handlers for custom business logic errors

async def business_logic_error_handler(request: Request, exc: BusinessLogicError):
    """Handle custom business logic errors"""
    
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    logger.warning(
        f"Business logic error in {request.method} {request.url.path}: {exc.message}",
        extra={
            "correlation_id": correlation_id,
            "error_code": exc.error_code,
            "status_code": exc.status_code
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "correlation_id": correlation_id,
            "type": "business_logic_error"
        }
    )

# Health check exception for monitoring

class HealthCheckError(Exception):
    """Health check related errors"""
    
    def __init__(self, service: str, message: str):
        self.service = service
        self.message = message
        super().__init__(f"{service}: {message}")

async def health_check_error_handler(request: Request, exc: HealthCheckError):
    """Handle health check errors"""
    
    correlation_id = getattr(request.state, 'correlation_id', str(uuid.uuid4()))
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": f"Health check failed for {exc.service}",
            "service": exc.service,
            "details": exc.message,
            "status_code": 503,
            "correlation_id": correlation_id,
            "type": "health_check_error"
        }
    )