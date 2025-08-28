"""
Bot Management Router

Migrated from api/src/handlers/bots.js to provide bot management functionality
within the FastAPI backend.
"""

from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse
import logging
from typing import Optional
import httpx
from datetime import datetime

from config.database import get_db_connection, get_db_transaction, get_qdrant_client
from config.settings import settings
from middleware.auth import get_current_user, AuthenticatedUser
from models.schemas import (
    CreateBotRequest, UpdateBotRequest, BotResponse, BotWithStatsResponse, BotListResponse,
    SuccessResponse, ErrorResponse
)
from utils.logging import log_service_call, log_service_result, log_external_service_call
from utils.helpers import current_timestamp, generate_uuid

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/debug/all-bots", response_model=dict)
async def debug_all_bots(
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Debug endpoint to see all bots in the database.
    This should only be used for debugging purposes.
    """
    try:
        async with get_db_connection() as conn:
            # Get all bots (no user filtering for debugging)
            all_bots = await conn.fetch("""
                SELECT id, name, description, website_url, user_id, created_at, updated_at
                FROM bots
                ORDER BY created_at DESC
            """)
            
            # Get current user's bots
            user_bots = await conn.fetch("""
                SELECT id, name, description, website_url, user_id, created_at, updated_at
                FROM bots
                WHERE user_id = $1
                ORDER BY created_at DESC
            """, current_user.id)
            
            return {
                "message": "Debug info",
                "current_user_id": str(current_user.id),
                "current_user_email": current_user.email,
                "total_bots_in_db": len(all_bots),
                "user_bots_count": len(user_bots),
                "all_bots": [
                    {
                        "id": str(bot['id']),
                        "name": bot['name'],
                        "user_id": str(bot['user_id']),
                        "created_at": bot['created_at'].isoformat() if bot['created_at'] else None
                    }
                    for bot in all_bots
                ],
                "user_bots": [
                    {
                        "id": str(bot['id']),
                        "name": bot['name'],
                        "user_id": str(bot['user_id']),
                        "created_at": bot['created_at'].isoformat() if bot['created_at'] else None
                    }
                    for bot in user_bots
                ]
            }
            
    except Exception as e:
        logger.error(f"Debug endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Debug endpoint error: {str(e)}"
        )

@router.get("/test-auth", response_model=dict)
async def test_auth(
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Test endpoint to verify authentication is working correctly.
    """
    return {
        "message": "Authentication working",
        "user_id": str(current_user.id),
        "user_email": current_user.email,
        "timestamp": datetime.utcnow().isoformat()
    }

@router.get("", response_model=BotListResponse)
async def get_bots(
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get all bots for a user.
    Migrated from api/src/handlers/bots.js getBots function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "BotsRouter",
        "get_bots",
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    # Debug: Log user information
    logger.info(f"Current user: {current_user}")
    logger.info(f"User ID: {current_user.id}")
    logger.info(f"User email: {current_user.email}")
    
    try:
        async with get_db_connection() as conn:
            # Get all bots for the user
            logger.info(f"Fetching bots for user_id: {current_user.id}")
            
            # First, let's check if the user exists in the auth.users table
            user_check = await conn.fetchrow("""
                SELECT id, email FROM auth.users WHERE id = $1
            """, current_user.id)
            
            if user_check:
                logger.info(f"User found in auth.users: {user_check['email']}")
            else:
                logger.warning(f"User {current_user.id} not found in auth.users table")
            
            # Get all bots for the user
            bot_rows = await conn.fetch("""
                SELECT id, name, description, website_url, user_id, created_at, updated_at
                FROM bots
                WHERE user_id = $1
                ORDER BY created_at DESC
            """, current_user.id)
            
            logger.info(f"Found {len(bot_rows)} bots for user {current_user.id}")
            
            # Debug: Log all bots found
            for bot in bot_rows:
                logger.info(f"Bot: {bot['name']} (ID: {bot['id']}, User: {bot['user_id']})")
            
            bots = []
            bot_ids = [row['id'] for row in bot_rows]
            
            # Get message counts for each bot
            messages_count_by_bot = {}
            documents_count_by_bot = {}
            
            if bot_ids:
                # Get conversations for these bots
                conversation_rows = await conn.fetch("""
                    SELECT id, bot_id
                    FROM conversations
                    WHERE bot_id = ANY($1)
                """, bot_ids)
                
                if conversation_rows:
                    conv_ids = [row['id'] for row in conversation_rows]
                    conv_id_to_bot_id = {row['id']: row['bot_id'] for row in conversation_rows}
                    
                    # Get message counts
                    message_rows = await conn.fetch("""
                        SELECT conversation_id
                        FROM messages
                        WHERE conversation_id = ANY($1)
                    """, conv_ids)
                    
                    for row in message_rows:
                        bot_id = conv_id_to_bot_id.get(row['conversation_id'])
                        if bot_id:
                            messages_count_by_bot[bot_id] = messages_count_by_bot.get(bot_id, 0) + 1
                
                # Get document counts
                document_rows = await conn.fetch("""
                    SELECT bot_id
                    FROM documents
                    WHERE bot_id = ANY($1)
                """, bot_ids)
                
                for row in document_rows:
                    bot_id = row['bot_id']
                    documents_count_by_bot[bot_id] = documents_count_by_bot.get(bot_id, 0) + 1
            
            # Build enriched bot responses
            for row in bot_rows:
                bot_dict = {
                    'id': str(row['id']),  # Convert UUID to string
                    'name': row['name'],
                    'description': row['description'],
                    'website_url': row['website_url'],
                    'user_id': str(row['user_id']),  # Convert UUID to string
                    'created_at': row['created_at'].isoformat() if row['created_at'] else None,
                    'updated_at': row['updated_at'].isoformat() if row['updated_at'] else None,
                    'messages_count': messages_count_by_bot.get(row['id'], 0),
                    'documents_count': documents_count_by_bot.get(row['id'], 0),
                    'status': 'active'  # Default status for dashboard compatibility
                }
                
                bots.append(bot_dict)
            
            log_service_result(
                logger,
                "BotsRouter",
                "get_bots",
                True,
                bots_count=len(bots),
                correlation_id=correlation_id
            )
            
            return BotListResponse(bots=bots, total=len(bots))
            
    except Exception as e:
        log_service_result(
            logger,
            "BotsRouter",
            "get_bots",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Get bots error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bots"
        )

@router.get("/{bot_id}", response_model=dict)
async def get_bot(
    bot_id: str,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get a specific bot.
    Migrated from api/src/handlers/bots.js getBot function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "BotsRouter",
        "get_bot",
        bot_id=bot_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_connection() as conn:
            bot_row = await conn.fetchrow("""
                SELECT id, name, description, website_url, user_id, created_at, updated_at
                FROM bots
                WHERE id = $1 AND user_id = $2
            """, bot_id, current_user.id)
            
            if not bot_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot not found or access denied"
                )
            
            log_service_result(
                logger,
                "BotsRouter",
                "get_bot",
                True,
                correlation_id=correlation_id
            )
            
            bot_data = BotResponse(
                id=str(bot_row['id']),  # Convert UUID to string
                name=bot_row['name'],
                description=bot_row['description'],
                website_url=bot_row['website_url'],
                user_id=str(bot_row['user_id']),  # Convert UUID to string
                created_at=bot_row['created_at'],
                updated_at=bot_row['updated_at']
            )
            
            return {"bot": bot_data}
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "BotsRouter",
            "get_bot",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Get bot error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bot"
        )

@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_bot(
    request: CreateBotRequest,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Create a new bot.
    Migrated from api/src/handlers/bots.js createBot function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "BotsRouter",
        "create_bot",
        name=request.name,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        bot_id = generate_uuid()
        now = current_timestamp()
        
        async with get_db_transaction() as conn:
            # Insert the bot
            await conn.execute("""
                INSERT INTO bots (id, name, description, website_url, user_id, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, 
                bot_id,
                request.name,
                request.description,
                request.website_url,
                current_user.id,
                now,
                now
            )
            
            logger.info(f"Successfully inserted bot into database with ID: {bot_id}")
        
        # Create a collection in Qdrant for this bot
        try:
            qdrant_client = get_qdrant_client()
            
            log_external_service_call(
                logger,
                "Qdrant",
                f"create_collection/{bot_id}",
                vector_size=1024
            )
            
            qdrant_client.create_collection(
                collection_name=bot_id,
                vectors_config={"size": 1024, "distance": "Cosine"}  # 1024 for Amazon Titan embeddings
            )
            
            logger.info(f"Successfully created Qdrant collection for bot {bot_id}")
            
        except Exception as qdrant_error:
            # Log error but don't fail the request
            logger.error(f"Failed to create Qdrant collection: {qdrant_error}", exc_info=True)
        
        # Fetch the created bot
        async with get_db_connection() as conn:
            bot_row = await conn.fetchrow("""
                SELECT id, name, description, website_url, user_id, created_at, updated_at
                FROM bots
                WHERE id = $1
            """, bot_id)
        
        log_service_result(
            logger,
            "BotsRouter",
            "create_bot",
            True,
            bot_id=bot_id,
            correlation_id=correlation_id
        )
        
        bot_data = BotResponse(
            id=str(bot_row['id']),  # Convert UUID to string
            name=bot_row['name'],
            description=bot_row['description'],
            website_url=bot_row['website_url'],
            user_id=str(bot_row['user_id']),  # Convert UUID to string
            created_at=bot_row['created_at'],
            updated_at=bot_row['updated_at']
        )
        
        return {"bot": bot_data}
        
    except Exception as e:
        log_service_result(
            logger,
            "BotsRouter",
            "create_bot",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Create bot error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create bot"
        )

@router.put("/{bot_id}", response_model=dict)
async def update_bot(
    bot_id: str,
    request: UpdateBotRequest,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Update a bot.
    Migrated from api/src/handlers/bots.js updateBot function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "BotsRouter",
        "update_bot",
        bot_id=bot_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_transaction() as conn:
            # Check if bot exists and belongs to user
            existing_bot = await conn.fetchrow("""
                SELECT id
                FROM bots
                WHERE id = $1 AND user_id = $2
            """, bot_id, current_user.id)
            
            if not existing_bot:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot not found or access denied"
                )
            
            # Build update query dynamically based on provided fields
            update_fields = []
            params = []
            param_count = 1
            
            if request.name is not None:
                update_fields.append(f"name = ${param_count}")
                params.append(request.name)
                param_count += 1
            
            if request.description is not None:
                update_fields.append(f"description = ${param_count}")
                params.append(request.description)
                param_count += 1
            
            if request.website_url is not None:
                update_fields.append(f"website_url = ${param_count}")
                params.append(request.website_url)
                param_count += 1
            
            if not update_fields:
                # No fields to update
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No fields provided for update"
                )
            
            # Add updated_at
            update_fields.append(f"updated_at = ${param_count}")
            params.append(current_timestamp())
            param_count += 1
            
            # Add WHERE conditions
            params.extend([bot_id, current_user.id])
            
            query = f"""
                UPDATE bots 
                SET {', '.join(update_fields)}
                WHERE id = ${param_count} AND user_id = ${param_count + 1}
            """
            
            await conn.execute(query, *params)
            
            # Fetch updated bot
            bot_row = await conn.fetchrow("""
                SELECT id, name, description, website_url, user_id, created_at, updated_at
                FROM bots
                WHERE id = $1
            """, bot_id)
        
        log_service_result(
            logger,
            "BotsRouter",
            "update_bot",
            True,
            correlation_id=correlation_id
        )
        
        bot_data = BotResponse(
            id=str(bot_row['id']),  # Convert UUID to string
            name=bot_row['name'],
            description=bot_row['description'],
            website_url=bot_row['website_url'],
            user_id=str(bot_row['user_id']),  # Convert UUID to string
            created_at=bot_row['created_at'],
            updated_at=bot_row['updated_at']
        )
        
        return {"bot": bot_data}
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "BotsRouter",
            "update_bot",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Update bot error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update bot"
        )

@router.delete("/{bot_id}", response_model=SuccessResponse)
async def delete_bot(
    bot_id: str,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Delete a bot.
    Migrated from api/src/handlers/bots.js deleteBot function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "BotsRouter",
        "delete_bot",
        bot_id=bot_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_transaction() as conn:
            # Check if bot exists and belongs to user
            existing_bot = await conn.fetchrow("""
                SELECT id
                FROM bots
                WHERE id = $1 AND user_id = $2
            """, bot_id, current_user.id)
            
            if not existing_bot:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot not found or access denied"
                )
            
            # Delete the bot (cascade should handle related records)
            await conn.execute("""
                DELETE FROM bots
                WHERE id = $1 AND user_id = $2
            """, bot_id, current_user.id)
        
        # Delete the collection in Qdrant
        try:
            qdrant_client = get_qdrant_client()
            
            log_external_service_call(
                logger,
                "Qdrant",
                f"delete_collection/{bot_id}"
            )
            
            qdrant_client.delete_collection(collection_name=bot_id)
            logger.info(f"Successfully deleted Qdrant collection for bot {bot_id}")
            
        except Exception as qdrant_error:
            # Log error but don't fail the request
            logger.error(f"Failed to delete Qdrant collection: {qdrant_error}", exc_info=True)
        
        log_service_result(
            logger,
            "BotsRouter",
            "delete_bot",
            True,
            correlation_id=correlation_id
        )
        
        return SuccessResponse(message="Bot deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "BotsRouter",
            "delete_bot",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Delete bot error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete bot"
        )