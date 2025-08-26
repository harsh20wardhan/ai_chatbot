"""
CORS Middleware

Migrated from api/src/middleware/cors.js to provide the same CORS behavior
in the FastAPI backend using built-in FastAPI CORS middleware.
"""

from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
import logging

from config.settings import settings

logger = logging.getLogger(__name__)

def setup_cors_middleware(app):
    """Setup CORS middleware for the FastAPI app"""
    
    # Define allowed origins
    allowed_origins = [
        'http://localhost:3000',
        'http://localhost:8787', 
        'http://127.0.0.1:3000',
        'http://127.0.0.1:8787'
    ]
    
    # For development, allow all origins
    if settings.ENVIRONMENT == "development":
        allowed_origins = ["*"]
    
    app.add_middleware(
        FastAPICORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
        max_age=86400,
    )
    
    logger.info("CORS middleware configured")
    logger.info(f"Allowed origins: {allowed_origins}")
    logger.info("CORS allows all origins in development mode")