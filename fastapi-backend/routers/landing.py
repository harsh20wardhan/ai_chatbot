"""
Landing Page Router

Provides public landing page functionality for unregistered users.
"""

from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse
import logging
import json
from typing import Optional, Dict, Any

from config.database import get_db_connection
from models.schemas import (
    LandingPageResponse, LandingPageRequest, LandingPageContent
)
from utils.logging import log_service_call, log_service_result
from utils.helpers import current_timestamp

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{page_type}", response_model=LandingPageResponse)
async def get_landing_page(
    page_type: str,
    http_request: Request
):
    """
    Get landing page content for a specific page type.
    This endpoint is public (no authentication required).
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "LandingRouter",
        "get_landing_page",
        page_type=page_type,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_connection() as conn:
            # Get landing page content
            page_row = await conn.fetchrow("""
                SELECT id, page_type, title, content, meta_data, is_active, created_at, updated_at
                FROM landing_page
                WHERE page_type = $1 AND is_active = true
            """, page_type)
            
            if not page_row:
                # Return default content if page doesn't exist
                if page_type == "home":
                    default_content = LandingPageContent(
                        hero_title="AI-Powered Chatbots for Your Business",
                        hero_subtitle="Create intelligent chatbots that understand your business and provide instant customer support",
                        features=[
                            {
                                "title": "AI-Powered Responses",
                                "description": "Advanced language models provide human-like conversations",
                                "icon": "🤖"
                            },
                            {
                                "title": "Easy Integration",
                                "description": "Simple widget that integrates with any website",
                                "icon": "🔗"
                            },
                            {
                                "title": "24/7 Availability",
                                "description": "Provide instant support to customers anytime",
                                "icon": "⏰"
                            }
                        ],
                        pricing_plans=[
                            {
                                "name": "Starter",
                                "price": "$29",
                                "period": "per month",
                                "features": ["1 Bot", "1000 messages/month", "Basic support"]
                            },
                            {
                                "name": "Professional",
                                "price": "$99",
                                "period": "per month",
                                "features": ["5 Bots", "10000 messages/month", "Priority support"]
                            }
                        ],
                        contact_info={
                            "email": "contact@logiquad.com",
                            "phone": "+1 (555) 123-4567",
                            "address": "123 AI Street, Tech City, TC 12345"
                        }
                    )
                    
                    return LandingPageResponse(
                        id="default",
                        page_type="home",
                        title="AI Chatbot Platform",
                        content=default_content,
                        meta_data={},
                        is_active=True,
                        created_at=current_timestamp(),
                        updated_at=None
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Page not found"
                    )
            
            # Parse content from JSON
            content_data = page_row['content']
            if isinstance(content_data, str):
                try:
                    content_data = json.loads(content_data)
                except (json.JSONDecodeError, TypeError):
                    content_data = {}
            
            # Parse meta_data from JSON
            meta_data = page_row['meta_data']
            if isinstance(meta_data, str):
                try:
                    meta_data = json.loads(meta_data)
                except (json.JSONDecodeError, TypeError):
                    meta_data = {}
            
            log_service_result(
                logger,
                "LandingRouter",
                "get_landing_page",
                True,
                correlation_id=correlation_id
            )
            
            return LandingPageResponse(
                id=str(page_row['id']),
                page_type=page_row['page_type'],
                title=page_row['title'],
                content=LandingPageContent(**content_data),
                meta_data=meta_data,
                is_active=page_row['is_active'],
                created_at=page_row['created_at'],
                updated_at=page_row['updated_at']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "LandingRouter",
            "get_landing_page",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Get landing page error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve landing page"
        )

