"""
Chat Router

Migrated from api/src/handlers/chat.js to provide RAG chat functionality
within the FastAPI backend.
"""

from fastapi import APIRouter, HTTPException, Request, status, Depends, Query
from fastapi.responses import JSONResponse
import logging
import json
from typing import Optional
import uuid

from config.database import get_db_connection, get_db_transaction
from middleware.auth import get_current_user, get_optional_user, AuthenticatedUser
from services.rag import rag_service
from models.schemas import (
    ChatRequest, ChatResponse, ConversationResponse, ConversationListResponse,
    ErrorResponse
)
from utils.logging import log_service_call, log_service_result
from utils.helpers import current_timestamp, generate_uuid

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("", response_model=ChatResponse)
async def process_chat(
    request: ChatRequest,
    http_request: Request,
    current_user: Optional[AuthenticatedUser] = Depends(get_optional_user)
):
    """
    Process a chat message using RAG.
    Migrated from api/src/handlers/chat.js processChat function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "ChatRouter",
        "process_chat",
        query=request.query[:30] + "..." if len(request.query) > 30 else request.query,
        bot_id=request.bot_id,
        conversation_id=request.conversation_id,
        correlation_id=correlation_id
    )
    
    try:
        # Verify the bot exists
        logger.info(f"Checking if bot exists: {request.bot_id}")
        
        async with get_db_connection() as conn:
            bot_row = await conn.fetchrow("""
                SELECT id, name, user_id, custom_prompt
                FROM bots 
                WHERE id = $1
            """, request.bot_id)
            
            if not bot_row:
                logger.warning(f"Bot not found: {request.bot_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot not found"
                )
            
            logger.info(f"Bot found: {bot_row['name']}")
        
        # Create or get conversation
        conversation_id = request.conversation_id
        if conversation_id:
            logger.info(f"Getting existing conversation: {conversation_id}")
            conversation = await _get_conversation(conversation_id, request.bot_id)
            if not conversation:
                logger.info("Creating new conversation, existing not found")
                conversation = await _create_conversation(request.bot_id, request.query)
                conversation_id = conversation['id']
        else:
            logger.info("No conversation ID provided, creating new conversation")
            conversation = await _create_conversation(request.bot_id, request.query)
            conversation_id = conversation['id']
        
        # Store user message in database
        logger.info("Storing user message in database")
        await _store_message(conversation_id, 'user', request.query)
        
        # Process chat using RAG service
        logger.info("Calling RAG service")
        rag_response = await rag_service.process_chat(
            query=request.query,
            bot_id=request.bot_id,
            conversation_id=conversation_id,
            message_history=[msg.dict() for msg in request.message_history],
            custom_prompt=bot_row['custom_prompt'] if bot_row else None
        )
        
        # Store assistant's response in database
        logger.info("Storing assistant message in database")
        await _store_message(
            conversation_id,
            'assistant',
            rag_response['answer'],
            metadata={
                'sources': rag_response['sources'],
                'tokens_used': rag_response['tokens_used']
            }
        )
        
        log_service_result(
            logger,
            "ChatRouter",
            "process_chat",
            True,
            conversation_id=conversation_id,
            tokens_used=rag_response['tokens_used'],
            correlation_id=correlation_id
        )
        
        return ChatResponse(
            answer=rag_response['answer'],
            answer_text=rag_response['answer_text'],
            answer_html=rag_response['answer_html'],
            sources=rag_response['sources'],
            tokens_used=rag_response['tokens_used'],
            conversation_id=conversation_id,
            error=rag_response.get('error')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "ChatRouter",
            "process_chat",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Chat processing error: {e}", exc_info=True)
        
        # Return error in expected format
        return ChatResponse(
            answer="I'm sorry, I'm having trouble processing your request right now. Please try again later.",
            answer_text="I'm sorry, I'm having trouble processing your request right now. Please try again later.",
            answer_html="<p>I'm sorry, I'm having trouble processing your request right now. Please try again later.</p>",
            sources=[],
            tokens_used=0,
            conversation_id=request.conversation_id or "new",
            error=f"Failed to process chat request: {str(e)}"
        )

@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    bot_id: Optional[str] = Query(None, description="Bot ID to get conversations for (optional)"),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get all conversations for a bot.
    Migrated from api/src/handlers/chat.js getConversations function
    """
    
    log_service_call(
        logger,
        "ChatRouter",
        "get_conversations",
        bot_id=bot_id,
        user_id=current_user.id
    )
    
    try:
        async with get_db_connection() as conn:
            if bot_id:
                # Verify bot ownership if bot_id is provided
                bot_row = await conn.fetchrow("""
                    SELECT id
                    FROM bots 
                    WHERE id = $1 AND user_id = $2
                """, bot_id, current_user.id)
                
                if not bot_row:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Bot not found or access denied"
                    )
            
            if bot_id:
                # Verify bot ownership first
                bot_row = await conn.fetchrow("""
                    SELECT id FROM bots
                    WHERE id = $1 AND user_id = $2
                """, bot_id, current_user.id)
                
                if not bot_row:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Bot not found or access denied"
                    )
                
                # Get conversations for the specific bot
                conversation_rows = await conn.fetch("""
                    SELECT id, bot_id, title, created_at, updated_at
                    FROM conversations
                    WHERE bot_id = $1
                    ORDER BY updated_at DESC
                """, bot_id)
            else:
                # Get all conversations for the user (through their bots)
                conversation_rows = await conn.fetch("""
                    SELECT c.id, c.bot_id, c.title, c.created_at, c.updated_at
                    FROM conversations c
                    JOIN bots b ON c.bot_id = b.id
                    WHERE b.user_id = $1
                    ORDER BY c.updated_at DESC
                """, current_user.id)
            
            conversations = [
                ConversationResponse(
                    id=str(row['id']),
                    bot_id=str(row['bot_id']),
                    messages=[],  # Messages not included in list view
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                for row in conversation_rows
            ]
            
            log_service_result(
                logger,
                "ChatRouter",
                "get_conversations",
                True,
                conversations_count=len(conversations)
            )
            
            return ConversationListResponse(
                conversations=conversations,
                total=len(conversations)
            )
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "ChatRouter",
            "get_conversations",
            False,
            error=str(e)
        )
        
        logger.error(f"Get conversations error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations"
        )

@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get a conversation with its messages.
    Migrated from api/src/handlers/chat.js getConversation function
    """
    
    log_service_call(
        logger,
        "ChatRouter",
        "get_conversation",
        conversation_id=conversation_id,
        user_id=current_user.id
    )
    
    try:
        async with get_db_connection() as conn:
            # Get conversation details with bot ownership check
            conversation_row = await conn.fetchrow("""
                SELECT c.id, c.bot_id, c.title, c.created_at, c.updated_at,
                       b.user_id as bot_user_id
                FROM conversations c
                JOIN bots b ON c.bot_id = b.id
                WHERE c.id = $1
            """, conversation_id)
            
            if not conversation_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found"
                )
            
            # Verify bot ownership
            if conversation_row['bot_user_id'] != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            # Get messages for the conversation
            message_rows = await conn.fetch("""
                SELECT role, content, created_at, metadata
                FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at ASC
            """, conversation_id)
            
            messages = [
                {
                    "role": row['role'],
                    "content": row['content']
                }
                for row in message_rows
            ]
            
            log_service_result(
                logger,
                "ChatRouter",
                "get_conversation",
                True,
                messages_count=len(messages)
            )
            
            return ConversationResponse(
                id=conversation_row['id'],
                bot_id=conversation_row['bot_id'],
                messages=messages,
                created_at=conversation_row['created_at'],
                updated_at=conversation_row['updated_at']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "ChatRouter",
            "get_conversation",
            False,
            error=str(e)
        )
        
        logger.error(f"Get conversation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversation"
        )

# Helper methods
async def _get_conversation(conversation_id: str, bot_id: str) -> Optional[dict]:
    """Get existing conversation"""
    try:
        async with get_db_connection() as conn:
            row = await conn.fetchrow("""
                SELECT id, bot_id, title, created_at, updated_at
                FROM conversations
                WHERE id = $1 AND bot_id = $2
            """, conversation_id, bot_id)
            
            if row:
                return {
                    'id': row['id'],
                    'bot_id': row['bot_id'],
                    'title': row['title'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at']
                }
            return None
    except Exception as e:
        logger.error(f"Error getting conversation: {e}", exc_info=True)
        return None

async def _create_conversation(bot_id: str, query: str) -> dict:
    """Create new conversation"""
    try:
        conversation_id = generate_uuid()
        title = query[:50] + ("..." if len(query) > 50 else "")
        now = current_timestamp()
        
        async with get_db_connection() as conn:
            await conn.execute("""
                INSERT INTO conversations (id, bot_id, title, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5)
            """, conversation_id, bot_id, title, now, now)
            
            return {
                'id': conversation_id,
                'bot_id': bot_id,
                'title': title,
                'created_at': now,
                'updated_at': now
            }
    except Exception as e:
        logger.error(f"Error creating conversation: {e}", exc_info=True)
        raise

async def _store_message(
    conversation_id: str,
    role: str,
    content: str,
    metadata: Optional[dict] = None
):
    """Store message in database"""
    try:
        # Convert metadata dict to JSON string if needed
        metadata_json = None
        if metadata:
            import json
            metadata_json = json.dumps(metadata) if isinstance(metadata, dict) else metadata
        
        async with get_db_connection() as conn:
            await conn.execute("""
                INSERT INTO messages (id, conversation_id, role, content, metadata, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, 
                generate_uuid(),
                conversation_id,
                role,
                content,
                metadata_json,
                current_timestamp()
            )
    except Exception as e:
        logger.error(f"Error storing message: {e}", exc_info=True)
        # Don't raise here as this is a secondary operation

# Attach helper methods to the module
import sys
current_module = sys.modules[__name__]
current_module._get_conversation = _get_conversation
current_module._create_conversation = _create_conversation
current_module._store_message = _store_message