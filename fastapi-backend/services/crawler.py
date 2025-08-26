"""
Crawler Service

Migrated from crawler_service.py and crawler/crawler.py to provide
website crawling functionality within the FastAPI backend.
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import uuid

from config.database import get_db_connection, get_db_transaction, get_qdrant_client, get_bedrock_client
from config.settings import settings
from utils.logging import log_service_call, log_service_result, log_external_service_call
from utils.helpers import current_timestamp, generate_uuid, chunk_text

logger = logging.getLogger(__name__)

class CrawlerService:
    """Service for website crawling operations"""
    
    def __init__(self):
        self.logger = logger
    
    async def crawl_website(
        self,
        url: str,
        max_pages: int = 20,
        exclude_patterns: Optional[List[str]] = None,
        job_id: Optional[str] = None,
        bot_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crawl a website and collect page content.
        Migrated from crawler/crawler.py
        """
        
        log_service_call(
            self.logger,
            "CrawlerService",
            "crawl_website",
            url=url,
            max_pages=max_pages,
            job_id=job_id,
            bot_id=bot_id
        )
        
        if exclude_patterns is None:
            exclude_patterns = []
        
        try:
            # Update job status to running if job_id provided
            if job_id:
                await self._update_job_status(job_id, "running")
            
            # Perform the crawl
            results = await self._crawl_pages(url, max_pages, exclude_patterns)
            
            # Store results in database if job_id and bot_id provided
            if job_id and bot_id and user_id:
                await self._store_crawl_results(job_id, bot_id, user_id, results)
            
            # Update job status to completed
            if job_id:
                await self._update_job_status(job_id, "completed", len(results))
            
            log_service_result(
                self.logger,
                "CrawlerService", 
                "crawl_website",
                True,
                pages_crawled=len(results)
            )
            
            return {
                "status": "completed",
                "pages_crawled": len(results),
                "job_id": job_id,
                "bot_id": bot_id,
                "results": results
            }
            
        except Exception as e:
            # Update job status to failed
            if job_id:
                await self._update_job_status(job_id, "failed", error=str(e))
            
            log_service_result(
                self.logger,
                "CrawlerService",
                "crawl_website", 
                False,
                error=str(e)
            )
            
            raise
    
    async def _crawl_pages(
        self,
        base_url: str,
        max_pages: int,
        exclude_patterns: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Internal method to crawl pages.
        Migrated from crawler/crawler.py with async support.
        """
        
        self.logger.info(f"Starting crawl for {base_url} with max_pages={max_pages}")
        
        visited = set()
        to_visit = [base_url]
        collected = []
        
        def is_same_domain(url: str) -> bool:
            """Check if URL is from the same domain"""
            return urlparse(url).netloc == urlparse(base_url).netloc
        
        def should_exclude(url: str) -> bool:
            """Check if URL should be excluded based on patterns"""
            return any(pattern in url for pattern in exclude_patterns)
        
        while to_visit and len(visited) < max_pages:
            url = to_visit.pop(0)
            
            if url in visited or not is_same_domain(url) or should_exclude(url):
                continue
            
            try:
                self.logger.info(f"Crawling: {url}")
                
                # Make HTTP request
                response = requests.get(url, timeout=10)
                if response.status_code != 200:
                    self.logger.warning(f"Failed {url}: HTTP {response.status_code}")
                    continue
                
                # Parse HTML content
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Extract title
                title = soup.find('title')
                title_text = title.get_text().strip() if title else "No title"
                
                # Remove navigation, footer, ads, and other non-content elements
                for tag in soup(["nav", "footer", "aside", "header", "script", "style", "meta", "link"]):
                    tag.decompose()
                
                # Get main content
                text = soup.get_text(separator=" ", strip=True)
                
                # Clean up whitespace
                text = ' '.join(text.split())
                
                if len(text) < 50:  # Skip pages with very little content
                    self.logger.info(f"Skipping {url}: too little content (only {len(text)} chars)")
                    continue
                
                # Collect page data
                page_data = {
                    'url': url,
                    'title': title_text,
                    'content': text,
                    'content_length': len(text),
                    'crawled_at': current_timestamp().isoformat()
                }
                collected.append(page_data)
                
                self.logger.info(f"Successfully crawled: {url} ({len(text)} chars)")
                
                # Find new links to crawl
                for a in soup.find_all("a", href=True):
                    next_url = urljoin(url, a['href'])
                    if next_url not in visited and next_url not in to_visit:
                        to_visit.append(next_url)
                
                visited.add(url)
                
            except Exception as e:
                self.logger.error(f"Failed to crawl {url}: {e}", exc_info=True)
                continue
        
        self.logger.info(f"Crawl completed. Total pages: {len(collected)}")
        return collected
    
    async def cancel_crawl(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel a crawl job.
        Migrated from crawler_service.py
        """
        
        log_service_call(
            self.logger,
            "CrawlerService",
            "cancel_crawl",
            job_id=job_id
        )
        
        try:
            # Update job status to cancelled
            await self._update_job_status(job_id, "cancelled")
            
            log_service_result(
                self.logger,
                "CrawlerService",
                "cancel_crawl",
                True
            )
            
            return {
                "status": "cancelled",
                "job_id": job_id
            }
            
        except Exception as e:
            log_service_result(
                self.logger,
                "CrawlerService",
                "cancel_crawl",
                False,
                error=str(e)
            )
            raise
    
    async def _update_job_status(
        self,
        job_id: str,
        status: str,
        pages_crawled: Optional[int] = None,
        error: Optional[str] = None
    ):
        """Update crawl job status in database"""
        
        try:
            async with get_db_connection() as conn:
                query = """
                    UPDATE crawl_jobs 
                    SET status = $1, updated_at = $2
                """
                params = [status, current_timestamp()]
                
                if pages_crawled is not None:
                    query += ", pages_crawled = $3"
                    params.append(pages_crawled)
                
                if status == "completed":
                    query += f", completed_at = ${len(params) + 1}"
                    params.append(current_timestamp())
                
                if error:
                    query += f", error = ${len(params) + 1}"
                    params.append(error)
                
                query += f" WHERE id = ${len(params) + 1}"
                params.append(job_id)
                
                await conn.execute(query, *params)
                
                self.logger.debug(f"Updated job {job_id} status to {status}")
                
        except Exception as e:
            self.logger.error(f"Failed to update job status: {e}", exc_info=True)
            # Don't raise here as this is a secondary operation
    
    async def _store_crawl_results(
        self,
        job_id: str,
        bot_id: str,
        user_id: str,
        results: List[Dict[str, Any]]
    ):
        """Store crawl results in database and process embeddings"""
        
        try:
            async with get_db_transaction() as conn:
                for result in results:
                    page_id = generate_uuid()
                    
                    # Store crawled page
                    await conn.execute("""
                        INSERT INTO crawled_pages (
                            id, crawl_job_id, bot_id, user_id, url, title, 
                            content, content_length, status, created_at
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """, 
                        page_id,
                        job_id,
                        bot_id,
                        user_id,
                        result['url'],
                        result['title'],
                        result['content'],
                        result['content_length'],
                        'processing',  # Changed from 'pending' to 'processing'
                        current_timestamp()
                    )
                    
                    # Process embeddings for this page
                    try:
                        await self._process_page_embeddings(conn, page_id, bot_id, user_id, result['content'])
                        
                        # Update page status to completed
                        await conn.execute("""
                            UPDATE crawled_pages 
                            SET status = 'completed', updated_at = $1, embedded_at = $2
                            WHERE id = $3
                        """, current_timestamp(), current_timestamp(), page_id)
                        
                    except Exception as e:
                        self.logger.error(f"Failed to process embeddings for page {page_id}: {e}", exc_info=True)
                        
                        # Update page status to failed
                        await conn.execute("""
                            UPDATE crawled_pages 
                            SET status = 'failed', updated_at = $1, error = $2
                            WHERE id = $3
                        """, current_timestamp(), str(e), page_id)
                
                self.logger.info(f"Stored and processed {len(results)} crawled pages for job {job_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to store crawl results: {e}", exc_info=True)
            raise
    
    async def _process_page_embeddings(
        self,
        conn,
        page_id: str,
        bot_id: str,
        user_id: str,
        content: str
    ):
        """Process embeddings for a crawled page"""
        
        try:
            # Split content into chunks
            chunks = chunk_text(content)
            self.logger.info(f"Page {page_id}: split into {len(chunks)} chunks")
            
            if not chunks:
                self.logger.warning(f"No chunks generated for page {page_id}")
                return
            
            # Generate embeddings using Bedrock
            embeddings = await self._generate_embeddings(chunks)
            self.logger.info(f"Generated {len(embeddings)} embeddings")
            
            # Ensure Qdrant collection exists
            await self._ensure_qdrant_collection(bot_id, len(embeddings[0]) if embeddings else 1024)
            
            # Prepare points for Qdrant
            points = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_id = generate_uuid()
                qdrant_point_id = generate_uuid()
                
                # Store in database - fix the JSON serialization issue
                await conn.execute("""
                    INSERT INTO embedding_chunks (
                        id, crawled_page_id, bot_id, user_id, chunk_index,
                        chunk_text, chunk_length, embedding_vector, qdrant_point_id,
                        created_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """, 
                    chunk_id,
                    page_id,
                    bot_id,
                    user_id,
                    i,
                    chunk,
                    len(chunk),
                    embedding,  # Store as array, not JSON string
                    qdrant_point_id,
                    current_timestamp()
                )
                
                # Prepare Qdrant point
                points.append({
                    "id": qdrant_point_id,
                    "vector": embedding,
                    "payload": {
                        "page_id": page_id,
                        "chunk_index": i,
                        "chunk": chunk,
                        "source_type": "crawled_page"
                    }
                })
            
            # Upsert points to Qdrant
            qdrant_client = get_qdrant_client()
            qdrant_client.upsert(
                collection_name=bot_id,
                points=points
            )
            
            self.logger.info(f"Successfully processed {len(points)} embeddings for page {page_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to process embeddings for page {page_id}: {e}", exc_info=True)
            raise
    
    async def _generate_embeddings(self, chunks: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks using Bedrock"""
        
        try:
            bedrock_client = get_bedrock_client()
            embeddings = []
            
            log_external_service_call(
                self.logger,
                "AWS Bedrock",
                f"invoke_model/amazon.titan-embed-text-v2:0",
                chunks_count=len(chunks)
            )
            
            for chunk in chunks:
                response = bedrock_client.invoke_model(
                    body=json.dumps({"inputText": chunk}),
                    modelId="amazon.titan-embed-text-v2:0",
                    accept="application/json",
                    contentType="application/json"
                )
                
                response_body = json.loads(response.get("body").read())
                embedding = response_body.get("embedding")
                
                if not embedding:
                    raise ValueError(f"No embedding in response: {response_body}")
                
                embeddings.append(embedding)
            
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings: {e}", exc_info=True)
            raise
    
    async def _ensure_qdrant_collection(self, collection_name: str, vector_size: int):
        """Ensure Qdrant collection exists"""
        
        try:
            qdrant_client = get_qdrant_client()
            
            # Check if collection exists
            collections = qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if collection_name not in collection_names:
                # Create collection
                from qdrant_client.models import Distance, VectorParams
                
                qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                
                self.logger.info(f"Created Qdrant collection: {collection_name}")
            else:
                self.logger.info(f"Qdrant collection already exists: {collection_name}")
            
        except Exception as e:
            # If collection already exists, that's fine
            if "already exists" in str(e):
                self.logger.info(f"Qdrant collection already exists: {collection_name}")
            else:
                self.logger.error(f"Failed to ensure Qdrant collection: {e}", exc_info=True)
                raise
    
    async def get_crawl_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get crawl job status"""
        
        try:
            async with get_db_connection() as conn:
                row = await conn.fetchrow("""
                    SELECT id, bot_id, url, max_depth, exclude_patterns, status, 
                           pages_crawled, created_at, updated_at, completed_at, error
                    FROM crawl_jobs 
                    WHERE id = $1
                """, job_id)
                
                if not row:
                    return None
                
                return {
                    "job_id": row['id'],
                    "bot_id": row['bot_id'],
                    "url": row['url'],
                    "max_depth": row['max_depth'],
                    "exclude_patterns": row['exclude_patterns'] or [],
                    "status": row['status'],
                    "pages_crawled": row['pages_crawled'] or 0,
                    "created_at": row['created_at'],
                    "updated_at": row['updated_at'],
                    "completed_at": row['completed_at'],
                    "error": row['error']
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get crawl status: {e}", exc_info=True)
            raise
    
    async def get_crawl_jobs_by_bot(self, bot_id: str, user_id: str) -> List[Dict[str, Any]]:
        """Get all crawl jobs for a bot"""
        
        try:
            async with get_db_connection() as conn:
                rows = await conn.fetch("""
                    SELECT id, bot_id, url, max_depth, exclude_patterns, status,
                           pages_crawled, created_at, updated_at, completed_at, error
                    FROM crawl_jobs 
                    WHERE bot_id = $1 AND user_id = $2
                    ORDER BY created_at DESC
                """, bot_id, user_id)
                
                return [
                    {
                        "id": row['id'],
                        "bot_id": row['bot_id'],
                        "url": row['url'],
                        "max_depth": row['max_depth'],
                        "exclude_patterns": row['exclude_patterns'] or [],
                        "status": row['status'],
                        "pages_crawled": row['pages_crawled'] or 0,
                        "created_at": row['created_at'],
                        "updated_at": row['updated_at'],
                        "completed_at": row['completed_at'],
                        "error": row['error']
                    }
                    for row in rows
                ]
                
        except Exception as e:
            self.logger.error(f"Failed to get crawl jobs: {e}", exc_info=True)
            raise
    
    async def delete_crawl_job(self, job_id: str, user_id: str) -> bool:
        """Delete a crawl job and its associated data"""
        
        try:
            async with get_db_transaction() as conn:
                # Delete crawled pages first (foreign key constraint)
                await conn.execute("""
                    DELETE FROM crawled_pages 
                    WHERE crawl_job_id = $1
                """, job_id)
                
                # Delete the job
                result = await conn.execute("""
                    DELETE FROM crawl_jobs 
                    WHERE id = $1 AND user_id = $2
                """, job_id, user_id)
                
                # Check if job was actually deleted
                if result == "DELETE 0":
                    return False
                
                self.logger.info(f"Deleted crawl job {job_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to delete crawl job: {e}", exc_info=True)
            raise

# Global service instance
crawler_service = CrawlerService()