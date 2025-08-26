"""
Authentication Middleware

Migrated from api/src/middleware/auth.js to provide Supabase JWT validation
using FastAPI dependency injection.
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

from config.database import get_supabase_admin_client
from config.settings import settings

logger = logging.getLogger(__name__)

# HTTP Bearer token scheme
security = HTTPBearer()

class AuthenticatedUser:
    """Represents an authenticated user"""
    
    def __init__(self, user_data: dict):
        self.id = user_data.get('id')
        self.email = user_data.get('email')
        self.user_metadata = user_data.get('user_metadata', {})
        self.app_metadata = user_data.get('app_metadata', {})
        self.created_at = user_data.get('created_at')
        self.updated_at = user_data.get('updated_at')
        self.raw_data = user_data
    
    def __str__(self):
        return f"AuthenticatedUser(id={self.id}, email={self.email})"

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> AuthenticatedUser:
    """
    Dependency to get the current authenticated user from JWT token.
    Migrated from api/src/middleware/auth.js
    """
    
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    try:
        # Get the token from the Authorization header
        token = credentials.credentials
        
        logger.debug(
            f"Validating JWT token",
            extra={
                "correlation_id": correlation_id,
                "token_length": len(token) if token else 0
            }
        )
        
        # Initialize Supabase admin client for user verification
        supabase = get_supabase_admin_client()
        
        # Verify JWT with Supabase (matching original implementation)
        response = supabase.auth.get_user(token)
        
        if response.user is None:
            logger.warning(
                f"JWT validation failed: no user found",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(response) if hasattr(response, 'error') else "No user"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Unauthorized",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = response.user
        
        logger.info(
            f"User authenticated successfully",
            extra={
                "correlation_id": correlation_id,
                "user_id": user.id,
                "user_email": user.email
            }
        )
        
        return AuthenticatedUser(user.model_dump())
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.warning(
            f"Authentication failed",
            extra={
                "correlation_id": correlation_id,
                "error": str(e)
            }
        )
        # Return 401 for authentication failures, not 500
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_optional_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[AuthenticatedUser]:
    """
    Dependency to get the current user if authenticated, None otherwise.
    Useful for endpoints that work with or without authentication.
    """
    
    if not credentials:
        return None
    
    try:
        # Use the same logic as get_current_user but don't raise exceptions
        request_with_creds = Request(request.scope)
        request_with_creds.state = request.state
        
        return await get_current_user(request_with_creds, credentials)
    except HTTPException:
        # Return None for authentication failures in optional auth
        return None
    except Exception as e:
        logger.warning(f"Optional authentication failed: {e}")
        return None

def setup_auth_middleware():
    """Setup authentication middleware"""
    logger.info("Authentication middleware configured")
    logger.info("Using Supabase for JWT validation")
    logger.info(f"Supabase URL: {settings.SUPABASE_URL}")

# Convenience aliases for common use cases
CurrentUser = Depends(get_current_user)
OptionalUser = Depends(get_optional_user)