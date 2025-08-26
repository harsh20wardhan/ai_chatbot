"""
Admin Router

Migrated from api/src/handlers/admin.js to provide admin functionality
within the FastAPI backend.
"""

from fastapi import APIRouter, HTTPException, Request, status, Depends, Query
from fastapi.responses import JSONResponse
import logging
from typing import Optional, List, Dict, Any

from config.database import get_db_connection
from middleware.auth import get_current_user, AuthenticatedUser
from models.schemas import (
    AdminStatsResponse, ErrorResponse
)
from utils.logging import log_service_call, log_service_result

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/stats", response_model=dict)
async def get_admin_stats(
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get admin statistics for the current user.
    Migrated from api/src/handlers/admin.js getStats function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "AdminRouter",
        "get_admin_stats",
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_connection() as conn:
            # Get basic counts
            bot_count_row = await conn.fetchrow("""
                SELECT COUNT(*) as count FROM bots WHERE user_id = $1
            """, current_user.id)
            
            document_count_row = await conn.fetchrow("""
                SELECT COUNT(*) as count FROM documents WHERE user_id = $1
            """, current_user.id)
            
            conversation_count_row = await conn.fetchrow("""
                SELECT COUNT(*) as count 
                FROM conversations c
                JOIN bots b ON c.bot_id = b.id
                WHERE b.user_id = $1
            """, current_user.id)
            
            message_count_row = await conn.fetchrow("""
                SELECT COUNT(*) as count 
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                JOIN bots b ON c.bot_id = b.id
                WHERE b.user_id = $1
            """, current_user.id)
            
            # Get recent activity (last 10 messages)
            recent_activity_rows = await conn.fetch("""
                SELECT m.created_at, m.role, m.conversation_id, 
                       c.bot_id, b.name as bot_name
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                JOIN bots b ON c.bot_id = b.id
                WHERE b.user_id = $1
                ORDER BY m.created_at DESC
                LIMIT 10
            """, current_user.id)
            
            # Get recent jobs
            recent_crawl_jobs = await conn.fetch("""
                SELECT id, bot_id, url, status, pages_crawled, created_at, updated_at, completed_at, error
                FROM crawl_jobs
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 5
            """, current_user.id)
            
            recent_embedding_jobs = await conn.fetch("""
                SELECT id, bot_id, status, documents_processed, total_documents, 
                       created_at, updated_at, completed_at, error
                FROM embedding_jobs
                WHERE user_id = $1
                ORDER BY created_at DESC
                LIMIT 5
            """, current_user.id)
            
            # Format response
            stats = {
                "bot_count": bot_count_row['count'],
                "document_count": document_count_row['count'],
                "conversation_count": conversation_count_row['count'],
                "message_count": message_count_row['count']
            }
            
            recent_activity = [
                {
                    "created_at": row['created_at'],
                    "role": row['role'],
                    "conversation_id": row['conversation_id'],
                    "bot_id": row['bot_id'],
                    "bot_name": row['bot_name']
                }
                for row in recent_activity_rows
            ]
            
            recent_jobs = {
                "crawl_jobs": [
                    {
                        "id": row['id'],
                        "bot_id": row['bot_id'],
                        "url": row['url'],
                        "status": row['status'],
                        "pages_crawled": row['pages_crawled'] or 0,
                        "created_at": row['created_at'],
                        "updated_at": row['updated_at'],
                        "completed_at": row['completed_at'],
                        "error": row['error']
                    }
                    for row in recent_crawl_jobs
                ],
                "embedding_jobs": [
                    {
                        "id": row['id'],
                        "bot_id": row['bot_id'],
                        "status": row['status'],
                        "documents_processed": row['documents_processed'] or 0,
                        "total_documents": row['total_documents'] or 0,
                        "created_at": row['created_at'],
                        "updated_at": row['updated_at'],
                        "completed_at": row['completed_at'],
                        "error": row['error']
                    }
                    for row in recent_embedding_jobs
                ]
            }
            
            log_service_result(
                logger,
                "AdminRouter",
                "get_admin_stats",
                True,
                correlation_id=correlation_id
            )
            
            return {
                "stats": stats,
                "recent_activity": recent_activity,
                "recent_jobs": recent_jobs
            }
            
    except Exception as e:
        log_service_result(
            logger,
            "AdminRouter",
            "get_admin_stats",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Get admin stats error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve admin statistics"
        )

@router.get("/logs", response_model=dict)
async def get_logs(
    http_request: Request,
    log_type: str = Query("all", alias="type", description="Type of logs to retrieve"),
    limit: int = Query(50, ge=1, le=200, description="Number of logs to retrieve"),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get logs for the current user.
    Migrated from api/src/handlers/admin.js getLogs function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "AdminRouter",
        "get_logs",
        user_id=current_user.id,
        log_type=log_type,
        limit=limit,
        correlation_id=correlation_id
    )
    
    try:
        logs = []
        
        async with get_db_connection() as conn:
            # Get crawl logs
            if log_type in ["all", "crawl"]:
                crawl_logs = await conn.fetch("""
                    SELECT id, bot_id, url, status, pages_crawled, created_at, updated_at, 
                           completed_at, error, 'crawl' as type
                    FROM crawl_jobs
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """, current_user.id, limit)
                
                logs.extend([dict(row) for row in crawl_logs])
            
            # Get embedding logs
            if log_type in ["all", "embedding"]:
                embedding_logs = await conn.fetch("""
                    SELECT id, bot_id, status, documents_processed, total_documents,
                           created_at, updated_at, completed_at, error, 'embedding' as type
                    FROM embedding_jobs
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                    LIMIT $2
                """, current_user.id, limit)
                
                logs.extend([dict(row) for row in embedding_logs])
            
            # Get chat logs (messages)
            if log_type in ["all", "chat"]:
                chat_logs = await conn.fetch("""
                    SELECT m.id, m.role, m.content, m.created_at, m.conversation_id,
                           c.bot_id, c.title as conversation_title, 'chat' as type
                    FROM messages m
                    JOIN conversations c ON m.conversation_id = c.id
                    JOIN bots b ON c.bot_id = b.id
                    WHERE b.user_id = $1
                    ORDER BY m.created_at DESC
                    LIMIT $2
                """, current_user.id, limit)
                
                # Format chat logs
                formatted_chat_logs = []
                for row in chat_logs:
                    log_entry = dict(row)
                    # Truncate content for log display
                    if log_entry['content'] and len(log_entry['content']) > 200:
                        log_entry['content'] = log_entry['content'][:200] + "..."
                    formatted_chat_logs.append(log_entry)
                
                logs.extend(formatted_chat_logs)
        
        # Sort all logs by creation date (most recent first)
        logs.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Limit to requested number
        logs = logs[:limit]
        
        log_service_result(
            logger,
            "AdminRouter",
            "get_logs",
            True,
            logs_count=len(logs),
            correlation_id=correlation_id
        )
        
        return {
            "logs": logs,
            "count": len(logs)
        }
        
    except Exception as e:
        log_service_result(
            logger,
            "AdminRouter",
            "get_logs",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Get logs error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve logs"
        )

@router.get("/jobs", response_model=dict)
async def get_active_jobs(
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get active jobs for the current user.
    Migrated from api/src/handlers/admin.js getJobs function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "AdminRouter",
        "get_active_jobs",
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_connection() as conn:
            # Get active crawl jobs
            crawl_jobs = await conn.fetch("""
                SELECT id, bot_id, url, status, pages_crawled, max_pages,
                       created_at, updated_at, error
                FROM crawl_jobs
                WHERE user_id = $1 AND status IN ('pending', 'running')
                ORDER BY created_at DESC
            """, current_user.id)
            
            # Get active embedding jobs
            embedding_jobs = await conn.fetch("""
                SELECT id, bot_id, status, documents_processed, total_documents,
                       created_at, updated_at, error
                FROM embedding_jobs
                WHERE user_id = $1 AND status IN ('pending', 'running')
                ORDER BY created_at DESC
            """, current_user.id)
            
            crawl_jobs_data = [
                {
                    "id": row['id'],
                    "bot_id": row['bot_id'],
                    "url": row['url'],
                    "status": row['status'],
                    "pages_crawled": row['pages_crawled'] or 0,
                    "max_pages": row['max_pages'],
                    "created_at": row['created_at'],
                    "updated_at": row['updated_at'],
                    "error": row['error']
                }
                for row in crawl_jobs
            ]
            
            embedding_jobs_data = [
                {
                    "id": row['id'],
                    "bot_id": row['bot_id'],
                    "status": row['status'],
                    "documents_processed": row['documents_processed'] or 0,
                    "total_documents": row['total_documents'] or 0,
                    "created_at": row['created_at'],
                    "updated_at": row['updated_at'],
                    "error": row['error']
                }
                for row in embedding_jobs
            ]
            
            active_job_count = len(crawl_jobs_data) + len(embedding_jobs_data)
            
            log_service_result(
                logger,
                "AdminRouter",
                "get_active_jobs",
                True,
                active_job_count=active_job_count,
                correlation_id=correlation_id
            )
            
            return {
                "crawl_jobs": crawl_jobs_data,
                "embedding_jobs": embedding_jobs_data,
                "active_job_count": active_job_count
            }
            
    except Exception as e:
        log_service_result(
            logger,
            "AdminRouter",
            "get_active_jobs",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Get active jobs error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve active jobs"
        )