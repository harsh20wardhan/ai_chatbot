"""
Widget Router

Migrated from api/src/handlers/widget.js to provide widget configuration
functionality within the FastAPI backend.
"""

from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse
import logging
import json
from typing import Optional, Dict, Any

from config.database import get_db_connection, get_db_transaction
from middleware.auth import get_current_user, AuthenticatedUser, get_optional_user
from models.schemas import (
    WidgetConfigResponse, UpdateWidgetConfigRequest,
    SuccessResponse, ErrorResponse
)
from utils.logging import log_service_call, log_service_result
from utils.helpers import current_timestamp

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{bot_id}/config", response_model=dict)
async def get_widget_config(
    bot_id: str,
    http_request: Request
):
    """
    Get widget configuration for a bot.
    This endpoint is public (no authentication required) as it's used by the widget.
    Migrated from api/src/handlers/widget.js getWidgetConfig function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "WidgetRouter",
        "get_widget_config",
        bot_id=bot_id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_connection() as conn:
            # Get bot details (no user verification needed for public widget config)
            bot_row = await conn.fetchrow("""
                SELECT id, name, settings
                FROM bots
                WHERE id = $1
            """, bot_id)
            
            if not bot_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot not found"
                )
            
            # Extract widget settings from bot settings
            settings = bot_row['settings'] or {}
            
            # Handle case where settings might be stored as JSON string
            if isinstance(settings, str):
                try:
                    settings = json.loads(settings)
                except (json.JSONDecodeError, TypeError):
                    settings = {}
            
            widget_settings = settings.get('widget', {})
            
            # Build widget configuration with defaults
            widget_config = {
                "bot_id": bot_row['id'],
                "name": bot_row['name'],
                "theme": widget_settings.get('theme', 'light'),
                "primary_color": widget_settings.get('primary_color', '#007BFF'),
                "position": widget_settings.get('position', 'bottom-right'),
                "welcome_message": widget_settings.get(
                    'welcome_message', 
                    f"Hi there! I'm {bot_row['name']}. How can I help you today?"
                ),
                "placeholder_text": widget_settings.get('placeholder_text', 'Ask me anything...'),
                "show_sources": widget_settings.get('show_sources', True)
            }
            
            log_service_result(
                logger,
                "WidgetRouter",
                "get_widget_config",
                True,
                correlation_id=correlation_id
            )
            
            return {"config": widget_config}
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "WidgetRouter",
            "get_widget_config",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Get widget config error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve widget configuration"
        )

@router.put("/{bot_id}/config", response_model=dict)
async def update_widget_config(
    bot_id: str,
    request: UpdateWidgetConfigRequest,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Update widget configuration for a bot.
    This endpoint requires authentication as it modifies bot settings.
    Migrated from api/src/handlers/widget.js updateWidgetConfig function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "WidgetRouter",
        "update_widget_config",
        bot_id=bot_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_transaction() as conn:
            # Verify bot ownership and get current settings
            bot_row = await conn.fetchrow("""
                SELECT id, settings
                FROM bots
                WHERE id = $1 AND user_id = $2
            """, bot_id, current_user.id)
            
            if not bot_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot not found or access denied"
                )
            
            # Get current settings
            existing_settings = bot_row['settings'] or {}
            
            # Handle case where settings might be stored as JSON string
            if isinstance(existing_settings, str):
                try:
                    existing_settings = json.loads(existing_settings)
                except (json.JSONDecodeError, TypeError):
                    existing_settings = {}
            
            existing_widget_settings = existing_settings.get('widget', {})
            
            # Prepare updates (only include non-None values)
            updates = {}
            if request.theme is not None:
                updates['theme'] = request.theme
            if request.primary_color is not None:
                updates['primary_color'] = request.primary_color
            if request.position is not None:
                updates['position'] = request.position
            if request.welcome_message is not None:
                updates['welcome_message'] = request.welcome_message
            if request.placeholder_text is not None:
                updates['placeholder_text'] = request.placeholder_text
            if request.show_sources is not None:
                updates['show_sources'] = request.show_sources
            
            # Merge with existing widget settings
            updated_widget_settings = {
                **existing_widget_settings,
                **updates
            }
            
            # Update the full settings object
            updated_settings = {
                **existing_settings,
                'widget': updated_widget_settings
            }
            
            # Save to database
            await conn.execute("""
                UPDATE bots
                SET settings = $1, updated_at = $2
                WHERE id = $3 AND user_id = $4
            """, updated_settings, current_timestamp(), bot_id, current_user.id)
            
            log_service_result(
                logger,
                "WidgetRouter",
                "update_widget_config",
                True,
                correlation_id=correlation_id
            )
            
            return {
                "message": "Widget configuration updated successfully",
                "config": updated_widget_settings
            }
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "WidgetRouter",
            "update_widget_config",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Update widget config error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update widget configuration"
        )

@router.get("/{bot_id}/settings", response_model=dict)
async def get_widget_settings(
    bot_id: str,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get full widget settings for a bot (authenticated endpoint for bot owners).
    Additional endpoint for comprehensive settings management
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "WidgetRouter",
        "get_widget_settings",
        bot_id=bot_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_connection() as conn:
            # Verify bot ownership and get settings
            bot_row = await conn.fetchrow("""
                SELECT id, name, settings, created_at, updated_at
                FROM bots
                WHERE id = $1 AND user_id = $2
            """, bot_id, current_user.id)
            
            if not bot_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot not found or access denied"
                )
            
            # Get full settings including widget configuration
            settings = bot_row['settings'] or {}
            widget_settings = settings.get('widget', {})
            
            log_service_result(
                logger,
                "WidgetRouter",
                "get_widget_settings",
                True,
                correlation_id=correlation_id
            )
            
            return {
                "bot_id": bot_row['id'],
                "bot_name": bot_row['name'],
                "widget_settings": widget_settings,
                "full_settings": settings,
                "last_updated": bot_row['updated_at']
            }
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "WidgetRouter",
            "get_widget_settings",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Get widget settings error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve widget settings"
        )

@router.post("/{bot_id}/reset-config", response_model=dict)
async def reset_widget_config(
    bot_id: str,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Reset widget configuration to defaults.
    Additional endpoint for resetting widget settings
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "WidgetRouter",
        "reset_widget_config",
        bot_id=bot_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_transaction() as conn:
            # Verify bot ownership and get current settings
            bot_row = await conn.fetchrow("""
                SELECT id, name, settings
                FROM bots
                WHERE id = $1 AND user_id = $2
            """, bot_id, current_user.id)
            
            if not bot_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot not found or access denied"
                )
            
            # Reset widget settings to defaults
            existing_settings = bot_row['settings'] or {}
            default_widget_settings = {
                "theme": "light",
                "primary_color": "#007BFF",
                "position": "bottom-right",
                "welcome_message": f"Hi there! I'm {bot_row['name']}. How can I help you today?",
                "placeholder_text": "Ask me anything...",
                "show_sources": True
            }
            
            # Update settings with reset widget configuration
            updated_settings = {
                **existing_settings,
                'widget': default_widget_settings
            }
            
            # Save to database
            await conn.execute("""
                UPDATE bots
                SET settings = $1, updated_at = $2
                WHERE id = $3 AND user_id = $4
            """, updated_settings, current_timestamp(), bot_id, current_user.id)
            
            log_service_result(
                logger,
                "WidgetRouter",
                "reset_widget_config",
                True,
                correlation_id=correlation_id
            )
            
            return {
                "message": "Widget configuration reset to defaults",
                "config": default_widget_settings
            }
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "WidgetRouter",
            "reset_widget_config",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Reset widget config error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset widget configuration"
        )