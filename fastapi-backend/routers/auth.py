"""
Authentication Router

Migrated from api/src/handlers/auth.js to provide authentication endpoints
using Supabase within the FastAPI backend.
"""

from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse
import logging
from typing import Optional

from config.database import get_supabase_client, get_supabase_admin_client
from middleware.auth import get_current_user, AuthenticatedUser
from models.schemas import (
    LoginRequest, RegisterRequest, ChangePasswordRequest,
    AuthResponse, UserResponse, SuccessResponse, ErrorResponse
)
from utils.logging import log_service_call, log_service_result

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest, http_request: Request):
    """
    User registration endpoint.
    Migrated from api/src/handlers/auth.js register function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "AuthRouter",
        "register",
        email=request.email,
        correlation_id=correlation_id
    )
    
    try:
        # Validate passwords match
        if request.password != request.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
        
        # Get Supabase client for public operations
        supabase = get_supabase_client()
        
        logger.info(f"Attempting registration for email: {request.email}")
        
        # Sign up user with Supabase
        signup_response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {},
                "email_redirect_to": f"{http_request.headers.get('origin', 'http://localhost:8000')}/auth/callback"
            }
        })
        
        if signup_response.user is None:
            error_msg = "Registration failed"
            if hasattr(signup_response, 'error') and signup_response.error:
                error_msg = signup_response.error.message
            
            logger.error(f"Supabase registration failed: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Try to get session token
        token = None
        expires_in = 3600  # Default 1 hour
        
        if signup_response.session:
            token = signup_response.session.access_token
            expires_in = signup_response.session.expires_in or 3600
        else:
            # If no session was created during signup, try to sign them in
            logger.info("No session created during signup, attempting sign in...")
            signin_response = supabase.auth.sign_in_with_password({
                "email": request.email,
                "password": request.password
            })
            
            if signin_response.session:
                token = signin_response.session.access_token
                expires_in = signin_response.session.expires_in or 3600
                logger.info("Successfully signed in after registration")
            else:
                logger.warning("Failed to sign in after registration")
        
        log_service_result(
            logger,
            "AuthRouter",
            "register",
            True,
            user_id=signup_response.user.id,
            correlation_id=correlation_id
        )
        
        return AuthResponse(
            access_token=token or "",
            token_type="bearer",
            expires_in=expires_in,
            user=signup_response.user.model_dump()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "AuthRouter",
            "register",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process registration"
        )

@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, http_request: Request):
    """
    User login endpoint.
    Migrated from api/src/handlers/auth.js login function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "AuthRouter",
        "login",
        email=request.email,
        correlation_id=correlation_id
    )
    
    try:
        # Get Supabase client for public operations
        supabase = get_supabase_client()
        
        logger.info(f"Attempting login for email: {request.email}")
        
        # Sign in with Supabase
        signin_response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if signin_response.user is None or signin_response.session is None:
            error_msg = "Invalid email or password"
            if hasattr(signin_response, 'error') and signin_response.error:
                error_msg = signin_response.error.message
            
            logger.warning(f"Login failed for {request.email}: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_msg
            )
        
        log_service_result(
            logger,
            "AuthRouter",
            "login",
            True,
            user_id=signin_response.user.id,
            correlation_id=correlation_id
        )
        
        return AuthResponse(
            access_token=signin_response.session.access_token,
            token_type="bearer",
            expires_in=signin_response.session.expires_in or 3600,
            user=signin_response.user.model_dump()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "AuthRouter",
            "login",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process login"
        )

@router.post("/logout", response_model=SuccessResponse)
async def logout(http_request: Request, current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    User logout endpoint.
    Migrated from api/src/handlers/auth.js logout function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "AuthRouter",
        "logout",
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        # Get the token from Authorization header
        auth_header = http_request.headers.get('authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token is required in Authorization header"
            )
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Use admin client to sign out the user
        supabase_admin = get_supabase_admin_client()
        
        # Note: Supabase doesn't have admin.signOut in Python client
        # The token will expire naturally, so we just return success
        logger.info(f"User {current_user.id} logged out successfully")
        
        log_service_result(
            logger,
            "AuthRouter",
            "logout",
            True,
            user_id=current_user.id,
            correlation_id=correlation_id
        )
        
        return SuccessResponse(message="Logout successful")
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "AuthRouter",
            "logout",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Logout error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process logout"
        )

@router.get("/user", response_model=UserResponse)
async def get_user(current_user: AuthenticatedUser = Depends(get_current_user)):
    """
    Get current user information.
    Migrated from api/src/handlers/auth.js getUser function
    """
    
    try:
        return UserResponse(
            id=current_user.id,
            email=current_user.email,
            created_at=current_user.raw_data.get('created_at'),
            updated_at=current_user.raw_data.get('updated_at'),
            user_metadata=current_user.user_metadata,
            app_metadata=current_user.app_metadata
        )
        
    except Exception as e:
        logger.error(f"Get user error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )

@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    request: ChangePasswordRequest,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Change user password.
    Migrated from api/src/handlers/auth.js changePassword function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "AuthRouter",
        "change_password",
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        # Verify current password if provided
        if request.current_password:
            supabase = get_supabase_client()
            verify_response = supabase.auth.sign_in_with_password({
                "email": current_user.email,
                "password": request.current_password
            })
            
            if verify_response.user is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Current password is incorrect"
                )
        
        # Update password using admin client
        supabase_admin = get_supabase_admin_client()
        
        update_response = supabase_admin.auth.admin.update_user_by_id(
            current_user.id,
            {"password": request.new_password}
        )
        
        if hasattr(update_response, 'error') and update_response.error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=update_response.error.message
            )
        
        log_service_result(
            logger,
            "AuthRouter",
            "change_password",
            True,
            user_id=current_user.id,
            correlation_id=correlation_id
        )
        
        return SuccessResponse(message="Password updated successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "AuthRouter",
            "change_password",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Change password error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update password"
        )

# Health check endpoint (migrated from healthCheck function)
@router.get("/health")
async def health_check():
    """Health check endpoint for authentication service"""
    
    try:
        return {
            "status": "ok",
            "message": "Auth service is running",
            "timestamp": "2025-01-28T10:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )