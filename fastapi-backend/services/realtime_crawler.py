"""
Realtime Crawler Service

Migrated from realtime_crawl_service.py to provide realtime crawling functionality
with WebSocket support within the FastAPI backend.
"""

import asyncio
import logging
import json
import uuid
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup

from config.database import (
    get_db_connection, get_db_transaction,
    get_qdrant_client, get_bedrock_client
)
from utils.logging import log_service_call, log_service_result, log_external_service_call
from utils.helpers import current_timestamp, generate_uuid, chunk_text

logger = logging.getLogger(__name__)

class RealtimeCrawlService:
    """Service for realtime website crawling with WebSocket updates"""
    
    def __init__(self):
        self.logger = logger
        self.embedding_model_id = "amazon.titan-embed-text-v2:0"
        self.embedding_dimension = 1024
    
    async def start_realtime_crawl(
        self,
        job_id: str,
        bot_id: str,
        user_id: str,
        base_url: str,
        max_pages: int = 20,
        exclude_patterns: Optional[List[str]] = None,
        websocket_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Start a realtime crawl with optional WebSocket updates.
        Migrated from realtime_crawl_service.py crawl_website_realtime function
        """
        
        log_service_call(
            self.logger,
            "RealtimeCrawlService",
            "start_realtime_crawl",
            job_id=job_id,
            bot_id=bot_id,
            base_url=base_url,
            max_pages=max_pages
        )
        
        try:
            # Update job status to running
            await self._update_crawl_job_status(job_id, "running")            
            # Initialize crawl state
            visited: Set[str] = set()
            to_visit: List[str] = [base_url]
            collected: List[Dict[str, Any]] = []
            pages_crawled = 0
            total_content_length = 0
            
            if exclude_patterns is None:
                exclude_patterns = []
            
            # Helper functions
            def is_same_domain(url: str) -> bool:
                return urlparse(url).netloc == urlparse(base_url).netloc
            
            def should_exclude(url: str) -> bool:
                return any(pattern in url for pattern in exclude_patterns)
            
            # Main crawling loop
            async with httpx.AsyncClient(timeout=10.0) as client:
                while to_visit and len(visited) < max_pages:
                    url = to_visit.pop(0)
                    
                    if url in visited or not is_same_domain(url) or should_exclude(url):
                        continue
                    
                    try:
                        self.logger.info(f"Crawling: {url}")
                        
                        # Emit crawling status via WebSocket
                        if websocket_callback:
                            await websocket_callback({
                                'type': 'crawl_status',
                                'status': 'crawling',
                                'url': url,
                                'pages_crawled': pages_crawled,
                                'total_pages': len(visited) + 1
                            })
                        
                        # Fetch the page
                        response = await client.get(url)
                        if response.status_code != 200:
                            self.logger.warning(f"Failed {url}: HTTP {response.status_code}")
                            continue
                        
                        # Parse content
                        soup = BeautifulSoup(response.text, "html.parser")
                        
                        # Extract title
                        title = soup.find('title')
                        title_text = title.get_text().strip() if title else "No title"
                        
                        # Remove non-content elements
                        for tag in soup(["nav", "footer", "aside", "header", "script", "style", "meta", "link"]):
                            tag.decompose()
                        
                        # Get main content
                        text = soup.get_text(separator=" ", strip=True)
                        text = ' '.join(text.split())  # Clean up whitespace
                        
                        if len(text) < 50:  # Skip pages with very little content
                            self.logger.info(f"Skipping {url}: too little content (only {len(text)} chars)")
                            continue
                        
                        # Store page in database
                        page_id = await self._store_crawled_page(
                            job_id, bot_id, user_id, url, title_text, text
                        )
                        
                        # Emit page crawled event
                        if websocket_callback:
                            await websocket_callback({
                                'type': 'page_crawled',
                                'page_id': str(page_id),
                                'url': url,
                                'title': title_text,
                                'content_length': len(text),
                                'pages_crawled': pages_crawled + 1
                            })
                        
                        # Start embedding process in background
                        asyncio.create_task(
                            self._embed_page_realtime(page_id, text, bot_id, user_id, websocket_callback)
                        )
                        
                        collected.append({
                            'url': url,
                            'title': title_text,
                            'content': text,
                            'content_length': len(text),
                            'page_id': page_id
                        })
                        
                        pages_crawled += 1
                        total_content_length += len(text)
                        
                        self.logger.info(f"Successfully crawled: {url} ({len(text)} chars)")
                        
                        # Update job progress periodically
                        if pages_crawled % 5 == 0:
                            await self._update_crawl_job_progress(job_id, pages_crawled)
                        
                        # Find new links
                        for a in soup.find_all("a", href=True):
                            next_url = urljoin(url, a['href'])
                            if next_url not in visited and next_url not in to_visit:
                                to_visit.append(next_url)
                        
                        visited.add(url)
                        
                    except Exception as e:
                        self.logger.error(f"Failed to crawl {url}: {e}")
                        if websocket_callback:
                            await websocket_callback({
                                'type': 'crawl_error',
                                'url': url,
                                'error': str(e)
                            })
            
            # Update final job status
            await self._update_crawl_job_status(job_id, "completed", pages_crawled)
            
            # Emit completion event
            if websocket_callback:
                await websocket_callback({
                    'type': 'crawl_completed',
                    'total_pages': len(collected),
                    'total_content_length': total_content_length,
                    'pages_crawled': pages_crawled
                })
            
            log_service_result(
                self.logger,
                "RealtimeCrawlService",
                "start_realtime_crawl",
                True,
                pages_crawled=pages_crawled,
                total_content_length=total_content_length
            )
            
            return {
                'status': 'completed',
                'job_id': job_id,
                'pages_crawled': pages_crawled,
                'total_content_length': total_content_length,
                'collected_pages': len(collected)
            }
            
        except Exception as e:
            # Update job status to failed
            await self._update_crawl_job_status(job_id, "failed", error=str(e))
            
            log_service_result(
                self.logger,
                "RealtimeCrawlService",
                "start_realtime_crawl",
                False,
                error=str(e)
            )
            raise
    
    async def _store_crawled_page(
        self,
        job_id: str,
        bot_id: str,
        user_id: str,
        url: str,
        title: str,
        content: str
    ) -> str:
        """Store crawled page in database"""
        
        try:
            page_id = generate_uuid()
            
            async with get_db_connection() as conn:
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
                    url,
                    title,
                    content,
                    len(content),
                    'pending',
                    current_timestamp()
                )
                
                self.logger.info(f"Stored crawled page {page_id} for URL: {url}")
                return page_id
                
        except Exception as e:
            self.logger.error(f"Failed to store crawled page: {e}", exc_info=True)
            raise
    
    async def _embed_page_realtime(
        self,
        page_id: str,
        text: str,
        bot_id: str,
        user_id: str,
        websocket_callback: Optional[callable] = None
    ):
        """Embed a single page in realtime with WebSocket updates"""
        
        try:
            self.logger.info(f"Starting embedding for page {page_id}")
            
            if websocket_callback:
                await websocket_callback({
                    'type': 'embedding_started',
                    'page_id': str(page_id),
                    'content_length': len(text)
                })
            
            # Split text into chunks
            chunks = chunk_text(text, chunk_size=500, overlap=50)
            self.logger.info(f"Split into {len(chunks)} chunks")
            
            if websocket_callback:
                await websocket_callback({
                    'type': 'embedding_progress',
                    'page_id': str(page_id),
                    'chunks_count': len(chunks),
                    'status': 'chunking_completed'
                })
            
            # Generate embeddings
            embeddings = await self._generate_embeddings_batch(chunks)
            self.logger.info(f"Generated {len(embeddings)} embeddings")
            
            if websocket_callback:
                await websocket_callback({
                    'type': 'embedding_progress',
                    'page_id': str(page_id),
                    'embeddings_count': len(embeddings),
                    'status': 'embeddings_generated'
                })
            
            # Ensure Qdrant collection exists
            await self._ensure_qdrant_collection(bot_id)
            
            # Store embeddings
            await self._store_page_embeddings(page_id, bot_id, user_id, chunks, embeddings)
            
            # Update page status
            await self._update_page_status(page_id, 'embedded')
            
            if websocket_callback:
                await websocket_callback({
                    'type': 'embedding_completed',
                    'page_id': str(page_id),
                    'chunks_stored': len(chunks),
                    'status': 'completed'
                })
            
            self.logger.info(f"Successfully embedded page {page_id} with {len(chunks)} chunks")
            
        except Exception as e:
            self.logger.error(f"Failed to embed page {page_id}: {e}", exc_info=True)
            
            # Update page status to failed
            await self._update_page_status(page_id, 'failed', str(e))
            
            if websocket_callback:
                await websocket_callback({
                    'type': 'embedding_error',
                    'page_id': str(page_id),
                    'error': str(e)
                })
    
    async def _generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts"""
        
        try:
            bedrock_client = get_bedrock_client()
            embeddings = []
            
            log_external_service_call(
                self.logger,
                "AWS Bedrock",
                f"batch_embed/{self.embedding_model_id}",
                batch_size=len(texts)
            )
            
            for i, text in enumerate(texts):
                if not text or len(text.strip()) == 0:
                    embeddings.append([0.0] * self.embedding_dimension)
                    continue
                
                response = bedrock_client.invoke_model(
                    body=json.dumps({"inputText": text}),
                    modelId=self.embedding_model_id,
                    accept="application/json",
                    contentType="application/json"
                )
                
                response_body = json.loads(response.get("body").read())
                embedding = response_body.get("embedding")
                
                if not embedding:
                    self.logger.warning(f"No embedding returned for text {i}")
                    embedding = [0.0] * self.embedding_dimension
                
                embeddings.append(embedding)
            
            return embeddings
            
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings: {e}", exc_info=True)
            raise
    
    async def _ensure_qdrant_collection(self, bot_id: str):
        """Ensure Qdrant collection exists for the bot"""
        
        try:
            qdrant_client = get_qdrant_client()
            
            # Check if collection exists
            collections = qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if bot_id not in collection_names:
                from qdrant_client.models import Distance, VectorParams
                
                qdrant_client.create_collection(
                    collection_name=bot_id,
                    vectors_config=VectorParams(
                        size=self.embedding_dimension,
                        distance=Distance.COSINE
                    )
                )
                self.logger.info(f"Created Qdrant collection: {bot_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to ensure Qdrant collection: {e}", exc_info=True)
            raise
    
    async def _store_page_embeddings(
        self,
        page_id: str,
        bot_id: str,
        user_id: str,
        chunks: List[str],
        embeddings: List[List[float]]
    ):
        """Store page embeddings in database and Qdrant"""
        
        try:
            qdrant_client = get_qdrant_client()
            
            # Prepare points for Qdrant
            points = []
            
            async with get_db_transaction() as conn:
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    chunk_id = generate_uuid()
                    qdrant_point_id = generate_uuid()
                    
                    # Store in database
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
                            "page_id": str(page_id),
                            "chunk_index": i,
                            "chunk": chunk,
                            "source_type": "crawled_page",
                            "bot_id": bot_id
                        }
                    })
            
            # Batch upsert to Qdrant
            if points:
                qdrant_client.upsert(
                    collection_name=bot_id,
                    points=points
                )
                
                self.logger.info(f"Stored {len(points)} embeddings for page {page_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to store page embeddings: {e}", exc_info=True)
            raise
    
    async def _update_crawl_job_status(
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
                
                self.logger.debug(f"Updated crawl job {job_id} status to {status}")
                
        except Exception as e:
            self.logger.error(f"Failed to update crawl job status: {e}", exc_info=True)
    
    async def _update_crawl_job_progress(self, job_id: str, pages_crawled: int):
        """Update crawl job progress"""
        
        try:
            async with get_db_connection() as conn:
                await conn.execute("""
                    UPDATE crawl_jobs 
                    SET pages_crawled = $1, updated_at = $2
                    WHERE id = $3
                """, pages_crawled, current_timestamp(), job_id)
                
        except Exception as e:
            self.logger.error(f"Failed to update crawl job progress: {e}", exc_info=True)
    
    async def _update_page_status(
        self,
        page_id: str,
        status: str,
        error: Optional[str] = None
    ):
        """Update crawled page status"""
        
        try:
            async with get_db_connection() as conn:
                query = """
                    UPDATE crawled_pages 
                    SET status = $1, updated_at = $2
                """
                params = [status, current_timestamp()]
                
                if status == "embedded":
                    query += ", embedded_at = $3"
                    params.append(current_timestamp())
                
                if error:
                    query += f", error = ${len(params) + 1}"
                    params.append(error)
                
                query += f" WHERE id = ${len(params) + 1}"
                params.append(page_id)
                
                await conn.execute(query, *params)
                
        except Exception as e:
            self.logger.error(f"Failed to update page status: {e}", exc_info=True)
    
    async def cancel_crawl(self, job_id: str) -> Dict[str, Any]:
        """Cancel a running crawl job"""
        
        log_service_call(
            self.logger,
            "RealtimeCrawlService",
            "cancel_crawl",
            job_id=job_id
        )
        
        try:
            async with get_db_connection() as conn:
                # Check if job exists and is running
                row = await conn.fetchrow("""
                    SELECT id, status FROM crawl_jobs WHERE id = $1
                """, job_id)
                
                if not row:
                    raise ValueError(f"Crawl job {job_id} not found")
                
                if row['status'] not in ['pending', 'running']:
                    raise ValueError(f"Cannot cancel job with status: {row['status']}")
                
                # Update job status to cancelled
                await conn.execute("""
                    UPDATE crawl_jobs 
                    SET status = 'cancelled', updated_at = $1, completed_at = $2
                    WHERE id = $3
                """, current_timestamp(), current_timestamp(), job_id)
                
                log_service_result(
                    self.logger,
                    "RealtimeCrawlService",
                    "cancel_crawl",
                    True,
                    job_id=job_id
                )
                
                return {
                    'status': 'cancelled',
                    'job_id': job_id,
                    'message': 'Crawl job cancelled successfully'
                }
                
        except Exception as e:
            log_service_result(
                self.logger,
                "RealtimeCrawlService",
                "cancel_crawl",
                False,
                error=str(e)
            )
            raise
    
    async def get_crawl_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get crawl job status and progress"""
        
        try:
            async with get_db_connection() as conn:
                row = await conn.fetchrow("""
                    SELECT id, bot_id, user_id, url, status, pages_crawled, max_pages,
                           created_at, updated_at, completed_at, error
                    FROM crawl_jobs 
                    WHERE id = $1
                """, job_id)
                
                if not row:
                    return None
                
                return {
                    'job_id': row['id'],
                    'bot_id': row['bot_id'],
                    'user_id': row['user_id'],
                    'url': row['url'],
                    'status': row['status'],
                    'pages_crawled': row['pages_crawled'] or 0,
                    'max_pages': row['max_pages'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'completed_at': row['completed_at'],
                    'error': row['error']
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get crawl status: {e}", exc_info=True)
            raise

# Global service instance
realtime_crawl_service = RealtimeCrawlService()