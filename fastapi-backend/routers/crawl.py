"""
Enhanced Crawling Router

Migrated from api/src/handlers/crawl.js and api/src/handlers/realtime_crawl.js
to provide enhanced website crawling functionality with deep crawling capabilities.
"""

from fastapi import APIRouter, HTTPException, Request, status, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
from typing import Optional, List
import asyncio

from config.database import get_db_connection, get_db_transaction
from middleware.auth import get_current_user, AuthenticatedUser
from services.crawler import crawler_service
from services.realtime_crawler import realtime_crawl_service
from models.schemas import (
    CrawlRequest, CrawlJobResponse, CrawlJobListResponse,
    RealtimeCrawlRequest, RealtimeCrawlResponse, CrawlStatusResponse,
    CrawledPageResponse, CrawledPageListResponse, CrawlJobDetailResponse,
    SuccessResponse, ErrorResponse
)
from utils.logging import log_service_call, log_service_result
from utils.helpers import current_timestamp, generate_uuid

logger = logging.getLogger(__name__)
router = APIRouter()

# Regular crawling endpoints

@router.post("", response_model=CrawlJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_crawl(
    request: CrawlRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Start an enhanced website crawl job with depth control.
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "EnhancedCrawlRouter",
        "start_crawl",
        url=request.url,
        bot_id=request.bot_id,
        max_depth=getattr(request, 'max_depth', 5),
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        # Verify bot ownership
        async with get_db_connection() as conn:
            bot_row = await conn.fetchrow("""
                SELECT id FROM bots
                WHERE id = $1 AND user_id = $2
            """, request.bot_id, current_user.id)
            
            if not bot_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot not found or access denied"
                )
        
        # Create crawl job with enhanced parameters
        job_id = generate_uuid()
        now = current_timestamp()
        
        # Extract enhanced parameters with defaults
        max_depth = getattr(request, 'max_depth', 5)
        max_pages = getattr(request, 'max_pages', 100)
        exclude_patterns = getattr(request, 'exclude_patterns', [])
        include_patterns = getattr(request, 'include_patterns', [])
        respect_robots_txt = getattr(request, 'respect_robots_txt', True)
        delay_between_requests = getattr(request, 'delay_between_requests', 1.0)
        
        async with get_db_transaction() as conn:
            await conn.execute("""
                INSERT INTO crawl_jobs (
                    id, bot_id, user_id, url, max_depth, max_pages, exclude_patterns,
                    include_patterns, respect_robots_txt, delay_between_requests,
                    status, created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """, 
                job_id,
                request.bot_id,
                current_user.id,
                request.url,
                max_depth,
                max_pages,
                exclude_patterns,
                include_patterns,
                respect_robots_txt,
                delay_between_requests,
                'pending',
                now,
                now
            )
        
        # Start enhanced crawling in background
        background_tasks.add_task(
            _run_enhanced_crawl_job,
            job_id,
            request.bot_id,
            current_user.id,
            request.url,
            max_pages,
            max_depth,
            exclude_patterns,
            include_patterns,
            respect_robots_txt,
            delay_between_requests
        )
        
        log_service_result(
            logger,
            "EnhancedCrawlRouter",
            "start_crawl",
            True,
            job_id=job_id,
            max_depth=max_depth,
            correlation_id=correlation_id
        )
        
        return CrawlJobResponse(
            job_id=job_id,
            message="Enhanced crawl job started successfully",
            status="pending"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "EnhancedCrawlRouter",
            "start_crawl",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Start enhanced crawl error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start enhanced crawl job"
        )

@router.get("/jobs", response_model=CrawlJobListResponse)
async def get_all_crawl_jobs(
    botId: Optional[str] = Query(None, description="Filter jobs by bot ID"),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get all crawl jobs for the current user, optionally filtered by bot ID.
    """
    
    log_service_call(
        logger,
        "CrawlRouter",
        "get_all_crawl_jobs",
        user_id=current_user.id,
        bot_id=botId
    )
    
    try:
        async with get_db_connection() as conn:
            # Build query based on whether botId filter is provided
            if botId:
                # Verify bot ownership first
                bot_row = await conn.fetchrow("""
                    SELECT id FROM bots
                    WHERE id = $1 AND user_id = $2
                """, botId, current_user.id)
                
                if not bot_row:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Bot not found or access denied"
                    )
                
                # Get crawl jobs for specific bot
                job_rows = await conn.fetch("""
                    SELECT id, bot_id, user_id, url, max_depth, exclude_patterns,
                           status, pages_crawled, created_at, updated_at, completed_at, error
                    FROM crawl_jobs
                    WHERE user_id = $1 AND bot_id = $2
                    ORDER BY created_at DESC
                """, current_user.id, botId)
            else:
                # Get all crawl jobs for user
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
                "CrawlRouter",
                "get_all_crawl_jobs",
                True,
                jobs_count=len(jobs)
            )
            
            return CrawlJobListResponse(jobs=jobs, total=len(jobs))
            
    except Exception as e:
        log_service_result(
            logger,
            "CrawlRouter",
            "get_all_crawl_jobs",
            False,
            error=str(e)
        )
        
        logger.error(f"Get all crawl jobs error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get crawl jobs"
        )

@router.get("/job/{job_id}", response_model=dict)
async def get_crawl_status(
    job_id: str,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get the status of a crawl job.
    Migrated from api/src/handlers/crawl.js getCrawlStatus function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "CrawlRouter",
        "get_crawl_status",
        job_id=job_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_connection() as conn:
            job_row = await conn.fetchrow("""
                SELECT id, bot_id, user_id, url, max_depth, exclude_patterns,
                       status, pages_crawled, created_at, updated_at, completed_at, error
                FROM crawl_jobs
                WHERE id = $1 AND user_id = $2
            """, job_id, current_user.id)
            
            if not job_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Crawl job not found"
                )
            
            job_data = {
                "id": str(job_row['id']),
                "bot_id": str(job_row['bot_id']),
                "user_id": str(job_row['user_id']),
                "url": job_row['url'],
                "max_depth": job_row['max_depth'],
                "exclude_patterns": job_row['exclude_patterns'],
                "status": job_row['status'],
                "pages_crawled": job_row['pages_crawled'] or 0,
                "created_at": job_row['created_at'],
                "updated_at": job_row['updated_at'],
                "completed_at": job_row['completed_at'],
                "error": job_row['error']
            }
            
            log_service_result(
                logger,
                "CrawlRouter",
                "get_crawl_status",
                True,
                correlation_id=correlation_id
            )
            
            return {"job": job_data}
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "CrawlRouter",
            "get_crawl_status",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Get crawl status error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get crawl status"
        )

@router.delete("/job/{job_id}", response_model=SuccessResponse)
async def cancel_crawl_job(
    job_id: str,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Cancel/delete a crawl job.
    Migrated from api/src/handlers/crawl.js deleteCrawlJob function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "CrawlRouter",
        "cancel_crawl_job",
        job_id=job_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        # Use crawler service to cancel the job
        result = await crawler_service.cancel_crawl(job_id, current_user.id)
        
        log_service_result(
            logger,
            "CrawlRouter",
            "cancel_crawl_job",
            True,
            correlation_id=correlation_id
        )
        
        return SuccessResponse(message=result['message'])
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        log_service_result(
            logger,
            "CrawlRouter",
            "cancel_crawl_job",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Cancel crawl job error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel crawl job"
        )

@router.get("/bot/{bot_id}", response_model=CrawlJobListResponse)
async def get_crawl_jobs_by_bot(
    bot_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get all crawl jobs for a specific bot.
    Migrated from api/src/handlers/crawl.js getCrawlJobsByBot function
    """
    
    log_service_call(
        logger,
        "CrawlRouter",
        "get_crawl_jobs_by_bot",
        bot_id=bot_id,
        user_id=current_user.id
    )
    
    try:
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
            
            # Get crawl jobs
            job_rows = await conn.fetch("""
                SELECT id, bot_id, user_id, url, max_depth, exclude_patterns,
                       status, pages_crawled, created_at, updated_at, completed_at, error
                FROM crawl_jobs
                WHERE bot_id = $1 AND user_id = $2
                ORDER BY created_at DESC
            """, bot_id, current_user.id)
            
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
                "CrawlRouter",
                "get_crawl_jobs_by_bot",
                True,
                jobs_count=len(jobs)
            )
            
            return CrawlJobListResponse(jobs=jobs, total=len(jobs))
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "CrawlRouter",
            "get_crawl_jobs_by_bot",
            False,
            error=str(e)
        )
        
        logger.error(f"Get crawl jobs error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get crawl jobs"
        )

# Realtime crawling endpoints

@router.post("/realtime", response_model=RealtimeCrawlResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_realtime_crawl(
    request: RealtimeCrawlRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Start a realtime crawl with WebSocket updates.
    Migrated from api/src/handlers/realtime_crawl.js startRealtimeCrawl function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "CrawlRouter",
        "start_realtime_crawl",
        url=request.url,
        bot_id=request.bot_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        # Verify bot ownership
        async with get_db_connection() as conn:
            bot_row = await conn.fetchrow("""
                SELECT id FROM bots
                WHERE id = $1 AND user_id = $2
            """, request.bot_id, current_user.id)
            
            if not bot_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot not found or access denied"
                )
        
        # Create crawl job
        job_id = generate_uuid()
        session_id = generate_uuid()
        now = current_timestamp()
        
        async with get_db_transaction() as conn:
            await conn.execute("""
                INSERT INTO crawl_jobs (
                    id, bot_id, user_id, url, max_depth, exclude_patterns,
                    status, created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, 
                job_id,
                request.bot_id,
                current_user.id,
                request.url,
                request.max_pages or 20,
                request.exclude_patterns or [],
                'pending',
                now,
                now
            )
        
        # Start realtime crawling in background
        background_tasks.add_task(
            _run_realtime_crawl_job,
            job_id,
            request.bot_id,
            current_user.id,
            request.url,
            request.max_pages or 20,
            request.exclude_patterns or [],
            session_id
        )
        
        log_service_result(
            logger,
            "CrawlRouter",
            "start_realtime_crawl",
            True,
            job_id=job_id,
            session_id=session_id,
            correlation_id=correlation_id
        )
        
        return RealtimeCrawlResponse(
            job_id=job_id,
            session_id=session_id,
            message="Realtime crawl job started successfully",
            websocket_url=f"/ws/crawl/{session_id}"  # WebSocket endpoint
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "CrawlRouter",
            "start_realtime_crawl",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Start realtime crawl error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start realtime crawl job"
        )

@router.get("/realtime/{job_id}", response_model=dict)
async def get_realtime_crawl_status(
    job_id: str,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get realtime crawl status.
    Migrated from api/src/handlers/realtime_crawl.js getRealtimeCrawlStatus function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "CrawlRouter",
        "get_realtime_crawl_status",
        job_id=job_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        # Get status from realtime crawl service
        status_data = await realtime_crawl_service.get_crawl_status(job_id)
        
        if not status_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crawl job not found"
            )
        
        # Verify ownership
        if status_data['user_id'] != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Crawl job not found"
            )
        
        log_service_result(
            logger,
            "CrawlRouter",
            "get_realtime_crawl_status",
            True,
            correlation_id=correlation_id
        )
        
        return {"job": status_data}
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "CrawlRouter",
            "get_realtime_crawl_status",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Get realtime crawl status error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get realtime crawl status"
        )

@router.get("/realtime/{job_id}/pages", response_model=CrawledPageListResponse)
async def get_crawled_pages(
    job_id: str,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get all crawled pages for a specific crawl job.
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "CrawlRouter",
        "get_crawled_pages",
        job_id=job_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_connection() as conn:
            # First verify the crawl job exists and user has access
            job_row = await conn.fetchrow("""
                SELECT cj.id, cj.bot_id, cj.user_id, cj.url
                FROM crawl_jobs cj
                WHERE cj.id = $1 AND cj.user_id = $2
            """, job_id, current_user.id)
            
            if not job_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Crawl job not found or access denied"
                )
            
            # Fetch all crawled pages for this job
            pages_rows = await conn.fetch("""
                SELECT 
                    cp.id,
                    cp.url,
                    cp.title,
                    cp.content_length,
                    cp.status,
                    cp.created_at,
                    cp.embedded_at
                FROM crawled_pages cp
                WHERE cp.crawl_job_id = $1
                ORDER BY cp.created_at DESC
            """, job_id)
            
            pages = []
            for row in pages_rows:
                pages.append(CrawledPageResponse(
                    id=str(row['id']),
                    url=row['url'],
                    title=row['title'] or "Untitled Page",
                    content_length=row['content_length'],
                    status=row['status'],
                    created_at=row['created_at'],
                    embedded_at=row['embedded_at']
                ))
            
            log_service_result(
                logger,
                "CrawlRouter",
                "get_crawled_pages",
                True,
                pages_count=len(pages)
            )
            
            return CrawledPageListResponse(
                pages=pages,
                total=len(pages)
            )
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "CrawlRouter",
            "get_crawled_pages",
            False,
            error=str(e)
        )
        
        logger.error(f"Get crawled pages error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch crawled pages"
        )

@router.get("/{job_id}/pages", response_model=CrawledPageListResponse)
async def get_crawl_job_pages(
    job_id: str,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get all crawled pages for a specific regular crawl job.
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "CrawlRouter",
        "get_crawl_job_pages",
        job_id=job_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_connection() as conn:
            # First verify the crawl job exists and user has access
            job_row = await conn.fetchrow("""
                SELECT cj.id, cj.bot_id, cj.user_id, cj.url
                FROM crawl_jobs cj
                WHERE cj.id = $1 AND cj.user_id = $2
            """, job_id, current_user.id)
            
            if not job_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Crawl job not found or access denied"
                )
            
            # Fetch all crawled pages for this job
            pages_rows = await conn.fetch("""
                SELECT 
                    cp.id,
                    cp.url,
                    cp.title,
                    cp.content_length,
                    cp.status,
                    cp.created_at,
                    cp.embedded_at
                FROM crawled_pages cp
                WHERE cp.crawl_job_id = $1
                ORDER BY cp.created_at DESC
            """, job_id)
            
            pages = []
            for row in pages_rows:
                pages.append(CrawledPageResponse(
                    id=str(row['id']),
                    url=row['url'],
                    title=row['title'] or "Untitled Page",
                    content_length=row['content_length'],
                    status=row['status'],
                    created_at=row['created_at'],
                    embedded_at=row['embedded_at']
                ))
            
            log_service_result(
                logger,
                "CrawlRouter",
                "get_crawl_job_pages",
                True,
                pages_count=len(pages)
            )
            
            return CrawledPageListResponse(
                pages=pages,
                total=len(pages)
            )
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "CrawlRouter",
            "get_crawl_job_pages",
            False,
            error=str(e)
        )
        
        logger.error(f"Get crawl job pages error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch crawled pages"
        )

@router.get("/pages/{page_id}", response_model=dict)
async def get_page_content(
    page_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get page content.
    Migrated from api/src/handlers/realtime_crawl.js getPageContent function
    """
    
    log_service_call(
        logger,
        "CrawlRouter",
        "get_page_content",
        page_id=page_id,
        user_id=current_user.id
    )
    
    try:
        async with get_db_connection() as conn:
            page_row = await conn.fetchrow("""
                SELECT id, url, title, content, content_length, status, created_at
                FROM crawled_pages
                WHERE id = $1 AND user_id = $2
            """, page_id, current_user.id)
            
            if not page_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Page not found"
                )
            
            page_data = {
                "id": page_row['id'],
                "url": page_row['url'],
                "title": page_row['title'],
                "content": page_row['content'],
                "content_length": page_row['content_length'],
                "status": page_row['status'],
                "created_at": page_row['created_at']
            }
            
            log_service_result(
                logger,
                "CrawlRouter",
                "get_page_content",
                True
            )
            
            return {"page": page_data}
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "CrawlRouter",
            "get_page_content",
            False,
            error=str(e)
        )
        
        logger.error(f"Get page content error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get page content"
        )

@router.delete("/pages/{page_id}", response_model=SuccessResponse)
async def delete_crawled_page(
    page_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Delete a crawled page.
    Migrated from api/src/handlers/realtime_crawl.js deleteCrawledPage function
    """
    
    log_service_call(
        logger,
        "CrawlRouter",
        "delete_crawled_page",
        page_id=page_id,
        user_id=current_user.id
    )
    
    try:
        async with get_db_transaction() as conn:
            # Get page info and verify ownership
            page_row = await conn.fetchrow("""
                SELECT id, bot_id FROM crawled_pages
                WHERE id = $1 AND user_id = $2
            """, page_id, current_user.id)
            
            if not page_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Page not found"
                )
            
            bot_id = page_row['bot_id']
            
            # Delete embedding chunks first
            await conn.execute("""
                DELETE FROM embedding_chunks
                WHERE crawled_page_id = $1
            """, page_id)
            
            # Delete the page
            await conn.execute("""
                DELETE FROM crawled_pages
                WHERE id = $1 AND user_id = $2
            """, page_id, current_user.id)
        
        # Try to delete from Qdrant (don't fail if this fails)
        try:
            from services.embedding import embedding_service
            await embedding_service.delete_document_embeddings(page_id, bot_id)
        except Exception as e:
            logger.warning(f"Failed to delete embeddings from Qdrant: {e}")
        
        log_service_result(
            logger,
            "CrawlRouter",
            "delete_crawled_page",
            True
        )
        
        return SuccessResponse(message="Page deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "CrawlRouter",
            "delete_crawled_page",
            False,
            error=str(e)
        )
        
        logger.error(f"Delete crawled page error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete page"
        )

# Background task functions

async def _run_enhanced_crawl_job(
    job_id: str,
    bot_id: str,
    user_id: str,
    url: str,
    max_pages: int,
    max_depth: int,
    exclude_patterns: List[str],
    include_patterns: List[str],
    respect_robots_txt: bool,
    delay_between_requests: float
):
    """Run enhanced crawl job in background"""
    
    try:
        await crawler_service.crawl_website(
            job_id=job_id,
            bot_id=bot_id,
            user_id=user_id,
            base_url=url,
            max_pages=max_pages,
            max_depth=max_depth,
            exclude_patterns=exclude_patterns,
            include_patterns=include_patterns,
            respect_robots_txt=respect_robots_txt,
            delay_between_requests=delay_between_requests
        )
    except Exception as e:
        logger.error(f"Background enhanced crawl job {job_id} failed: {e}", exc_info=True)

async def _run_realtime_crawl_job(
    job_id: str,
    bot_id: str,
    user_id: str,
    url: str,
    max_pages: int,
    exclude_patterns: List[str],
    session_id: str
):
    """Run realtime crawl job in background"""
    
    try:
        # TODO: Implement WebSocket callback for realtime updates
        # For now, run without WebSocket updates
        await realtime_crawl_service.start_realtime_crawl(
            job_id=job_id,
            bot_id=bot_id,
            user_id=user_id,
            base_url=url,
            max_pages=max_pages,
            exclude_patterns=exclude_patterns,
            websocket_callback=None  # TODO: Implement WebSocket support
        )
    except Exception as e:
        logger.error(f"Background realtime crawl job {job_id} failed: {e}", exc_info=True)