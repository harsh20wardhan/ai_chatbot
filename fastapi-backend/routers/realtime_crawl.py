"""
Realtime Crawling Router

Provides realtime crawling endpoints that were expected by the frontend
but missing from the main crawl router.
"""

from fastapi import APIRouter, HTTPException, Request, status, Depends
import logging

from config.database import get_db_connection
from middleware.auth import get_current_user, AuthenticatedUser
from models.schemas import CrawlJobListResponse, CrawlJobDetailResponse
from utils.logging import log_service_call, log_service_result

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/jobs", response_model=CrawlJobListResponse)
async def get_realtime_crawl_jobs(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get all realtime crawl jobs for the current user.
    This endpoint matches the frontend expectation for /api/realtime-crawl/jobs
    """
    
    log_service_call(
        logger,
        "RealtimeCrawlRouter",
        "get_realtime_crawl_jobs",
        user_id=current_user.id
    )
    
    try:
        async with get_db_connection() as conn:
            # Get crawl jobs (same as regular crawl jobs for now)
            job_rows = await conn.fetch("""
                SELECT id, bot_id, user_id, url, max_depth, exclude_patterns,
                       status, pages_crawled, created_at, updated_at, completed_at, error
                FROM crawl_jobs
                WHERE user_id = $1
                ORDER BY created_at DESC
            """, current_user.id)
            
            jobs = [
                CrawlJobDetailResponse(
                    id=str(row['id']),
                    bot_id=str(row['bot_id']),
                    url=row['url'],
                    max_depth=row['max_depth'],
                    exclude_patterns=row['exclude_patterns'],
                    status=row['status'],
                    pages_crawled=row['pages_crawled'] or 0,
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    completed_at=row['completed_at'],
                    error=row['error']
                )
                for row in job_rows
            ]
            
            log_service_result(
                logger,
                "RealtimeCrawlRouter",
                "get_realtime_crawl_jobs",
                True,
                jobs_count=len(jobs)
            )
            
            return CrawlJobListResponse(jobs=jobs, total=len(jobs))
            
    except Exception as e:
        log_service_result(
            logger,
            "RealtimeCrawlRouter",
            "get_realtime_crawl_jobs",
            False,
            error=str(e)
        )
        
        logger.error(f"Get realtime crawl jobs error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get realtime crawl jobs"
        )