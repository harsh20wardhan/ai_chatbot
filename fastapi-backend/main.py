"""
FastAPI Backend - Main Application Entry Point

This is the main FastAPI application that consolidates all services
previously running as separate Flask microservices and replaces the
Cloudflare Workers API with full compatibility.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import uuid
from contextlib import asynccontextmanager

from config.settings import settings
from config.database import init_database_pool, close_database_pool

# Import all middleware
from middleware.cors import setup_cors_middleware
from middleware.auth import setup_auth_middleware
from middleware.error_handler import (
    ErrorHandlerMiddleware, 
    business_logic_error_handler,
    health_check_error_handler,
    BusinessLogicError,
    HealthCheckError
)
from middleware.performance import (
    PerformanceMiddleware,
    RequestSizeMiddleware,
    RateLimitingMiddleware
)

from utils.logging import setup_logging
from routers import (
    auth,
    bots,
    crawl,
    realtime_crawl,
    documents,
    embeddings,
    chat,
    admin,
    analytics,
    widget,
    health
)

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    
    # Startup
    logger.info("Starting FastAPI backend...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    try:
        # Initialize database connection pool
        await init_database_pool()
        logger.info("Database connection pool initialized")
        
        # Test database connection if available
        from config.database import get_db_pool
        db_pool = get_db_pool()
        if db_pool:
            try:
                from config.database import get_db_connection
                async with get_db_connection() as conn:
                    await conn.fetchval("SELECT 1")
                logger.info("Direct database connection test successful")
            except Exception as e:
                logger.warning(f"Direct database connection test failed: {e}")
        else:
            logger.info("Using Supabase REST API instead of direct database connection")
        
        # Test external services
        try:
            from config.database import get_qdrant_client
            qdrant_client = get_qdrant_client()
            collections = qdrant_client.get_collections()
            logger.info(f"Qdrant connection successful - {len(collections.collections)} collections")
        except Exception as e:
            logger.warning(f"Qdrant connection failed: {e}")
        
        try:
            from config.database import get_bedrock_client
            bedrock_client = get_bedrock_client()
            if bedrock_client:
                logger.info("AWS Bedrock client initialized successfully")
            else:
                logger.warning("Bedrock client not available")
        except Exception as e:
            logger.warning(f"Bedrock connection failed: {e}")
        
        try:
            from config.database import get_supabase_admin_client
            supabase = get_supabase_admin_client()
            if supabase:
                logger.info("Supabase connection successful")
            else:
                logger.warning("Supabase client not available")
        except Exception as e:
            logger.warning(f"Supabase connection failed: {e}")
        
        logger.info("FastAPI backend startup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to start FastAPI backend: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down FastAPI backend...")
    
    try:
        # Close database connection pool
        await close_database_pool()
        logger.info("Database connection pool closed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    
    logger.info("FastAPI backend shutdown completed")

# Create FastAPI application
app = FastAPI(
    title="FastAPI Backend",
    description="Migrated from Cloudflare Workers API - provides bot management, document processing, and RAG chat functionality",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan
)

# Add security middleware
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS.split(",") if settings.ALLOWED_HOSTS else ["*"]
    )

# Add performance and monitoring middleware (order matters - these should be early)
app.add_middleware(
    RateLimitingMiddleware,
    requests_per_minute=getattr(settings, 'RATE_LIMIT_PER_MINUTE', 60)
)

app.add_middleware(
    RequestSizeMiddleware,
    max_request_size=getattr(settings, 'MAX_REQUEST_SIZE', 50 * 1024 * 1024)
)

app.add_middleware(
    PerformanceMiddleware,
    slow_request_threshold=getattr(settings, 'SLOW_REQUEST_THRESHOLD', 1.0)
)

# Add error handling middleware
app.add_middleware(ErrorHandlerMiddleware)

# Setup authentication
setup_auth_middleware()

# Add CORS middleware (should be last)
setup_cors_middleware(app)

# Add exception handlers for custom exceptions
app.add_exception_handler(BusinessLogicError, business_logic_error_handler)
app.add_exception_handler(HealthCheckError, health_check_error_handler)

# Global exception handler for unhandled exceptions
@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception):
    """Handle internal server errors"""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.error(
        f"Unhandled internal server error: {str(exc)}",
        extra={"correlation_id": correlation_id},
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "correlation_id": correlation_id,
            "type": "internal_server_error"
        }
    )

# Include routers with proper prefixes
app.include_router(
    health.router,
    tags=["Health"]
)

app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Authentication"]
)

app.include_router(
    bots.router,
    prefix="/api/bots",
    tags=["Bots"]
)

app.include_router(
    documents.router,
    prefix="/api/documents",
    tags=["Documents"]
)

app.include_router(
    crawl.router,
    prefix="/api/crawl",
    tags=["Crawling"]
)

app.include_router(
    realtime_crawl.router,
    prefix="/api/realtime-crawl",
    tags=["Realtime Crawling"]
)

app.include_router(
    embeddings.router,
    prefix="/api/embeddings",
    tags=["Embeddings"]
)

app.include_router(
    chat.router,
    prefix="/api/chat",
    tags=["Chat"]
)

app.include_router(
    admin.router,
    prefix="/api/admin",
    tags=["Admin"]
)

app.include_router(
    analytics.router,
    prefix="/api/analytics",
    tags=["Analytics"]
)

app.include_router(
    widget.router,
    prefix="/api/widget",
    tags=["Widget"]
)

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint providing basic API information"""
    return {
        "message": "FastAPI Backend is running",
        "version": "1.0.0",
        "status": "healthy",
        "docs_url": "/docs" if settings.ENVIRONMENT != "production" else None,
        "environment": settings.ENVIRONMENT
    }

# API info endpoint
@app.get("/api", tags=["Root"])
async def api_info():
    """API information endpoint"""
    return {
        "name": "FastAPI Backend API",
        "version": "1.0.0",
        "description": "Migrated from Cloudflare Workers API",
        "endpoints": {
            "authentication": "/api/auth",
            "bots": "/api/bots",
            "documents": "/api/documents",
            "crawling": "/api/crawl",
            "embeddings": "/api/embeddings",
            "chat": "/api/chat",
            "admin": "/api/admin",
            "analytics": "/api/analytics",
            "widget": "/api/widget",
            "health": "/health"
        }
    }

# Development server runner
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=getattr(settings, 'HOST', '0.0.0.0'),
        port=getattr(settings, 'PORT', 8000),
        reload=settings.ENVIRONMENT == "development",
        log_level=getattr(settings, 'LOG_LEVEL', 'info').lower(),
        access_log=True
    )