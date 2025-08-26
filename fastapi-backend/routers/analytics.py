"""
Analytics Router

Migrated from api/src/handlers/analytics.js to provide analytics functionality
within the FastAPI backend.
"""

from fastapi import APIRouter, HTTPException, Request, status, Depends, Query
from fastapi.responses import JSONResponse
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from config.database import get_db_connection
from middleware.auth import get_current_user, AuthenticatedUser
from models.schemas import (
    ErrorResponse
)
from utils.logging import log_service_call, log_service_result

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/bot-stats", response_model=dict)
async def get_bot_stats(
    http_request: Request,
    bot_id: str = Query(..., alias="botId", description="Bot ID to get analytics for"),
    range_period: str = Query("7d", alias="range", description="Time range: 7d, 30d, or 90d"),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get analytics statistics for a specific bot.
    Migrated from api/src/handlers/analytics.js getBotStats function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "AnalyticsRouter",
        "get_bot_stats",
        bot_id=bot_id,
        range_period=range_period,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        # Validate range parameter
        if range_period not in ["7d", "30d", "90d"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Range must be one of: 7d, 30d, 90d"
            )
        
        # Calculate date range
        now = datetime.utcnow()
        days_back = {"7d": 7, "30d": 30, "90d": 90}[range_period]
        start_date = now - timedelta(days=days_back)
        
        async with get_db_connection() as conn:
            # Verify bot ownership
            bot_row = await conn.fetchrow("""
                SELECT id FROM bots
                WHERE id = $1 AND user_id = $2
            """, bot_id, current_user.id)
            
            if not bot_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot not found or access denied"
                )
            
            # Get conversations in the date range
            conversation_rows = await conn.fetch("""
                SELECT id, created_at
                FROM conversations
                WHERE bot_id = $1 AND created_at >= $2
                ORDER BY created_at DESC
            """, bot_id, start_date)
            
            conversation_ids = [row['id'] for row in conversation_rows]
            unique_users = len(conversation_rows)  # Proxy for unique users
            
            # Initialize stats
            total_messages = 0
            daily_usage_map = defaultdict(int)
            user_message_contents = []
            
            if conversation_ids:
                # Get messages in the date range
                message_rows = await conn.fetch("""
                    SELECT created_at, role, content, conversation_id
                    FROM messages
                    WHERE conversation_id = ANY($1) AND created_at >= $2
                    ORDER BY created_at DESC
                """, conversation_ids, start_date)
                
                total_messages = len(message_rows)
                
                # Process messages for daily usage and top questions
                for row in message_rows:
                    # Daily usage tracking
                    date_key = row['created_at'].strftime('%Y-%m-%d')
                    daily_usage_map[date_key] += 1
                    
                    # Collect user messages for top questions analysis
                    if row['role'] == 'user' and row['content']:
                        content = row['content'].strip()[:80]  # First 80 chars
                        if content:
                            user_message_contents.append(content)
            
            # Calculate top questions (most frequent user message patterns)
            question_frequency = defaultdict(int)
            for content in user_message_contents:
                question_frequency[content] += 1
            
            top_questions = [
                {"question": question, "count": count}
                for question, count in sorted(
                    question_frequency.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:5]
            ]
            
            # Build daily usage array covering the entire range
            daily_usage = []
            current_date = start_date.date()
            end_date = now.date()
            
            while current_date <= end_date:
                date_key = current_date.strftime('%Y-%m-%d')
                daily_usage.append({
                    "date": date_key,
                    "messages": daily_usage_map[date_key]
                })
                current_date += timedelta(days=1)
            
            # Calculate average response time (placeholder - would need more sophisticated tracking)
            average_response_time = 0  # Not implemented in original either
            
            log_service_result(
                logger,
                "AnalyticsRouter",
                "get_bot_stats",
                True,
                total_messages=total_messages,
                unique_users=unique_users,
                correlation_id=correlation_id
            )
            
            return {
                "totalMessages": total_messages,
                "uniqueUsers": unique_users,
                "averageResponseTime": average_response_time,
                "topQuestions": top_questions,
                "dailyUsage": daily_usage
            }
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "AnalyticsRouter",
            "get_bot_stats",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Get bot stats error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compute analytics"
        )

@router.get("/bot-usage/{bot_id}", response_model=dict)
async def get_bot_usage(
    bot_id: str,
    http_request: Request,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get detailed usage analytics for a bot.
    Additional endpoint for more detailed usage tracking
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "AnalyticsRouter",
        "get_bot_usage",
        bot_id=bot_id,
        days=days,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        async with get_db_connection() as conn:
            # Verify bot ownership
            bot_row = await conn.fetchrow("""
                SELECT id, name FROM bots
                WHERE id = $1 AND user_id = $2
            """, bot_id, current_user.id)
            
            if not bot_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot not found or access denied"
                )
            
            # Get conversation and message statistics
            stats_row = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT c.id) as total_conversations,
                    COUNT(m.id) as total_messages,
                    COUNT(CASE WHEN m.role = 'user' THEN 1 END) as user_messages,
                    COUNT(CASE WHEN m.role = 'assistant' THEN 1 END) as bot_messages,
                    AVG(LENGTH(m.content)) as avg_message_length
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE c.bot_id = $1 AND c.created_at >= $2
            """, bot_id, start_date)
            
            # Get hourly usage pattern
            hourly_usage_rows = await conn.fetch("""
                SELECT 
                    EXTRACT(HOUR FROM m.created_at) as hour,
                    COUNT(*) as message_count
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.bot_id = $1 AND m.created_at >= $2
                GROUP BY EXTRACT(HOUR FROM m.created_at)
                ORDER BY hour
            """, bot_id, start_date)
            
            # Get most active days
            daily_activity_rows = await conn.fetch("""
                SELECT 
                    DATE(m.created_at) as date,
                    COUNT(*) as message_count,
                    COUNT(DISTINCT m.conversation_id) as conversation_count
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE c.bot_id = $1 AND m.created_at >= $2
                GROUP BY DATE(m.created_at)
                ORDER BY message_count DESC
                LIMIT 10
            """, bot_id, start_date)
            
            # Format hourly usage (fill in missing hours with 0)
            hourly_usage = {row['hour']: row['message_count'] for row in hourly_usage_rows}
            hourly_pattern = [
                {"hour": hour, "messages": hourly_usage.get(hour, 0)}
                for hour in range(24)
            ]
            
            # Format daily activity
            daily_activity = [
                {
                    "date": row['date'].strftime('%Y-%m-%d'),
                    "messages": row['message_count'],
                    "conversations": row['conversation_count']
                }
                for row in daily_activity_rows
            ]
            
            log_service_result(
                logger,
                "AnalyticsRouter",
                "get_bot_usage",
                True,
                correlation_id=correlation_id
            )
            
            return {
                "bot_name": bot_row['name'],
                "period_days": days,
                "summary": {
                    "total_conversations": stats_row['total_conversations'] or 0,
                    "total_messages": stats_row['total_messages'] or 0,
                    "user_messages": stats_row['user_messages'] or 0,
                    "bot_messages": stats_row['bot_messages'] or 0,
                    "avg_message_length": round(float(stats_row['avg_message_length'] or 0), 2)
                },
                "hourly_pattern": hourly_pattern,
                "top_active_days": daily_activity
            }
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "AnalyticsRouter",
            "get_bot_usage",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Get bot usage error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get bot usage analytics"
        )

@router.get("/overview", response_model=dict)
async def get_analytics_overview(
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get overall analytics overview for all user's bots.
    Additional endpoint for dashboard overview
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "AnalyticsRouter",
        "get_analytics_overview",
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_connection() as conn:
            # Get overall statistics
            overview_row = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT b.id) as total_bots,
                    COUNT(DISTINCT c.id) as total_conversations,
                    COUNT(DISTINCT d.id) as total_documents,
                    COUNT(m.id) as total_messages
                FROM bots b
                LEFT JOIN conversations c ON b.id = c.bot_id
                LEFT JOIN documents d ON b.id = d.bot_id
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE b.user_id = $1
            """, current_user.id)
            
            # Get bot-wise statistics
            bot_stats_rows = await conn.fetch("""
                SELECT 
                    b.id,
                    b.name,
                    COUNT(DISTINCT c.id) as conversations,
                    COUNT(DISTINCT d.id) as documents,
                    COUNT(m.id) as messages,
                    MAX(m.created_at) as last_activity
                FROM bots b
                LEFT JOIN conversations c ON b.id = c.bot_id
                LEFT JOIN documents d ON b.id = d.bot_id
                LEFT JOIN messages m ON c.id = m.conversation_id
                WHERE b.user_id = $1
                GROUP BY b.id, b.name
                ORDER BY messages DESC
            """, current_user.id)
            
            # Get recent activity (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent_activity_row = await conn.fetchrow("""
                SELECT 
                    COUNT(DISTINCT c.id) as new_conversations,
                    COUNT(m.id) as new_messages
                FROM conversations c
                LEFT JOIN messages m ON c.id = m.conversation_id
                JOIN bots b ON c.bot_id = b.id
                WHERE b.user_id = $1 AND c.created_at >= $2
            """, current_user.id, seven_days_ago)
            
            # Format bot statistics
            bot_statistics = [
                {
                    "bot_id": row['id'],
                    "bot_name": row['name'],
                    "conversations": row['conversations'] or 0,
                    "documents": row['documents'] or 0,
                    "messages": row['messages'] or 0,
                    "last_activity": row['last_activity']
                }
                for row in bot_stats_rows
            ]
            
            log_service_result(
                logger,
                "AnalyticsRouter",
                "get_analytics_overview",
                True,
                correlation_id=correlation_id
            )
            
            return {
                "overview": {
                    "total_bots": overview_row['total_bots'] or 0,
                    "total_conversations": overview_row['total_conversations'] or 0,
                    "total_documents": overview_row['total_documents'] or 0,
                    "total_messages": overview_row['total_messages'] or 0
                },
                "recent_activity": {
                    "new_conversations_7d": recent_activity_row['new_conversations'] or 0,
                    "new_messages_7d": recent_activity_row['new_messages'] or 0
                },
                "bot_statistics": bot_statistics
            }
            
    except Exception as e:
        log_service_result(
            logger,
            "AnalyticsRouter",
            "get_analytics_overview",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Get analytics overview error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get analytics overview"
        )