"""
Enhanced Crawler Service

Migrated from crawler_service.py and crawler/crawler.py to provide
advanced website crawling functionality with deep crawling capabilities.
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urlunparse
import uuid
import re
import time
from collections import deque
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

from config.database import get_db_connection, get_db_transaction, get_qdrant_client, get_bedrock_client
from config.settings import settings
from utils.logging import log_service_call, log_service_result, log_external_service_call
from utils.helpers import current_timestamp, generate_uuid, chunk_text

logger = logging.getLogger(__name__)

class EnhancedCrawlerService:
    """Enhanced service for website crawling operations with deep crawling capabilities"""
    
    def __init__(self):
        self.logger = logger
        self.session = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.lock = threading.Lock()
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def crawl_website(
        self,
        url: str,
        max_pages: int = 100,  # Increased default
        max_depth: int = 5,     # New depth parameter
        exclude_patterns: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None,
        job_id: Optional[str] = None,
        bot_id: Optional[str] = None,
        user_id: Optional[str] = None,
        respect_robots_txt: bool = True,
        delay_between_requests: float = 1.0
    ) -> Dict[str, Any]:
        """
        Enhanced crawl a website with depth control and better content extraction.
        """
        
        log_service_call(
            self.logger,
            "EnhancedCrawlerService",
            "crawl_website",
            url=url,
            max_pages=max_pages,
            max_depth=max_depth,
            job_id=job_id,
            bot_id=bot_id
        )
        
        if exclude_patterns is None:
            exclude_patterns = []
        if include_patterns is None:
            include_patterns = []
        
        try:
            # Update job status to running if job_id provided
            if job_id:
                await self._update_job_status(job_id, "running")
            
            # Perform the enhanced crawl
            results = await self._deep_crawl_pages(
                url, max_pages, max_depth, exclude_patterns, 
                include_patterns, respect_robots_txt, delay_between_requests
            )
            
            # Store results in database if job_id and bot_id provided
            if job_id and bot_id and user_id:
                await self._store_crawl_results(job_id, bot_id, user_id, results)
            
            # Update job status to completed
            if job_id:
                await self._update_job_status(job_id, "completed", len(results))
            
            log_service_result(
                self.logger,
                "EnhancedCrawlerService", 
                "crawl_website",
                True,
                pages_crawled=len(results),
                max_depth_reached=max_depth
            )
            
            return {
                "status": "completed",
                "pages_crawled": len(results),
                "max_depth_reached": max_depth,
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
                "EnhancedCrawlerService",
                "crawl_website", 
                False,
                error=str(e)
            )
            
            raise
    
    async def _deep_crawl_pages(
        self,
        base_url: str,
        max_pages: int,
        max_depth: int,
        exclude_patterns: List[str],
        include_patterns: List[str],
        respect_robots_txt: bool,
        delay_between_requests: float
    ) -> List[Dict[str, Any]]:
        """
        Enhanced deep crawling with depth control and better content extraction.
        """
        
        self.logger.info(f"Starting deep crawl for {base_url} with max_pages={max_pages}, max_depth={max_depth}")
        
        # Parse base URL
        parsed_base = urlparse(base_url)
        base_domain = parsed_base.netloc
        base_scheme = parsed_base.scheme
        
        # Initialize tracking structures
        visited_urls: Set[str] = set()
        url_queue: deque = deque([(base_url, 0)])  # (url, depth)
        collected_pages: List[Dict[str, Any]] = []
        
        # Robots.txt handling
        robots_rules = {}
        if respect_robots_txt:
            robots_rules = await self._parse_robots_txt(base_url)
        
        # Crawl pages with depth control
        while url_queue and len(visited_urls) < max_pages:
            current_url, current_depth = url_queue.popleft()
            
            # Skip if already visited or depth exceeded
            if current_url in visited_urls or current_depth > max_depth:
                continue
            
            # Check robots.txt rules
            if respect_robots_txt and self._is_url_disallowed(current_url, robots_rules):
                self.logger.info(f"Skipping {current_url}: disallowed by robots.txt")
                continue
            
            # Check exclusion/inclusion patterns
            if not self._should_crawl_url(current_url, exclude_patterns, include_patterns):
                continue
            
            try:
                self.logger.info(f"Crawling depth {current_depth}: {current_url}")
                
                # Fetch and parse page
                page_data = await self._fetch_and_parse_page(current_url, current_depth)
                
                if page_data and page_data['content_length'] >= 100:  # Increased minimum content threshold
                    collected_pages.append(page_data)
                    self.logger.info(f"Successfully crawled: {current_url} (depth {current_depth}, {page_data['content_length']} chars)")
                    
                    # Find new links for next depth level
                    if current_depth < max_depth:
                        new_links = await self._extract_links(page_data['soup'], current_url, base_domain, base_scheme)
                        
                        # Add new links to queue with incremented depth
                        for link in new_links:
                            if link not in visited_urls and link not in [url for url, _ in url_queue]:
                                url_queue.append((link, current_depth + 1))
                
                visited_urls.add(current_url)
                
                # Respect rate limiting
                if delay_between_requests > 0:
                    await asyncio.sleep(delay_between_requests)
                
            except Exception as e:
                self.logger.error(f"Failed to crawl {current_url}: {e}", exc_info=True)
                visited_urls.add(current_url)  # Mark as visited to avoid infinite loops
                continue
        
        self.logger.info(f"Deep crawl completed. Total pages: {len(collected_pages)}, Max depth reached: {max_depth}")
        return collected_pages
    
    async def _fetch_and_parse_page(self, url: str, depth: int) -> Optional[Dict[str, Any]]:
        """
        Fetch and parse a single page with enhanced content extraction.
        """
        
        try:
            # Use aiohttp for better async performance
            async with self.session.get(url, allow_redirects=True) as response:
                if response.status != 200:
                    self.logger.warning(f"Failed {url}: HTTP {response.status}")
                    return None
                
                content_type = response.headers.get('content-type', '')
                if 'text/html' not in content_type.lower():
                    self.logger.info(f"Skipping {url}: not HTML content ({content_type})")
                    return None
                
                html_content = await response.text()
                
                # Parse HTML with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Enhanced content extraction
                title = self._extract_title(soup)
                main_content = self._extract_main_content(soup)
                metadata = self._extract_metadata(soup)
                
                # Clean and process content
                cleaned_content = self._clean_content(main_content)
                
                if len(cleaned_content) < 100:
                    self.logger.info(f"Skipping {url}: insufficient content ({len(cleaned_content)} chars)")
                    return None
                
                return {
                    'url': url,
                    'title': title,
                    'content': cleaned_content,
                    'content_length': len(cleaned_content),
                    'depth': depth,
                    'metadata': metadata,
                    'soup': soup,  # Keep soup for link extraction
                    'crawled_at': current_timestamp().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}", exc_info=True)
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title with fallbacks"""
        
        # Try multiple title sources
        title = soup.find('title')
        if title and title.get_text().strip():
            return title.get_text().strip()
        
        # Try h1 tags
        h1 = soup.find('h1')
        if h1 and h1.get_text().strip():
            return h1.get_text().strip()
        
        # Try meta title
        meta_title = soup.find('meta', attrs={'name': 'title'})
        if meta_title and meta_title.get('content'):
            return meta_title.get('content').strip()
        
        # Try og:title
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        if og_title and og_title.get('content'):
            return og_title.get('content').strip()
        
        return "No title"
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content using multiple strategies"""
        
        # Remove unwanted elements
        for tag in soup(["nav", "footer", "aside", "header", "script", "style", "meta", "link", "noscript"]):
            tag.decompose()
        
        # Try to find main content areas
        main_content = ""
        
        # Strategy 1: Look for semantic HTML5 elements
        main_elements = soup.find_all(['main', 'article', 'section'])
        if main_elements:
            for element in main_elements:
                main_content += element.get_text(separator=" ", strip=True) + " "
        
        # Strategy 2: Look for content divs with common class names
        content_classes = ['content', 'main-content', 'post-content', 'entry-content', 'article-content']
        for class_name in content_classes:
            content_divs = soup.find_all(class_=re.compile(class_name, re.I))
            for div in content_divs:
                main_content += div.get_text(separator=" ", strip=True) + " "
        
        # Strategy 3: Look for divs with high text density
        if not main_content.strip():
            divs = soup.find_all('div')
            best_div = None
            best_score = 0
            
            for div in divs:
                text = div.get_text(separator=" ", strip=True)
                if len(text) > 200:  # Minimum content length
                    # Calculate text density (text length / total HTML length)
                    html_length = len(str(div))
                    if html_length > 0:
                        density = len(text) / html_length
                        if density > best_score:
                            best_score = density
                            best_div = div
            
            if best_div:
                main_content = best_div.get_text(separator=" ", strip=True)
        
        # Fallback: use body text if no main content found
        if not main_content.strip():
            main_content = soup.get_text(separator=" ", strip=True)
        
        return main_content
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract useful metadata from the page"""
        
        metadata = {}
        
        # Meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content
        
        # Structured data (JSON-LD)
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    metadata['json_ld'] = data
                elif isinstance(data, list):
                    metadata['json_ld'] = data
            except:
                pass
        
        # Open Graph tags
        og_tags = soup.find_all('meta', property=re.compile(r'^og:'))
        for tag in og_tags:
            property_name = tag.get('property', '')
            content = tag.get('content', '')
            if property_name and content:
                metadata[property_name] = content
        
        return metadata
    
    def _clean_content(self, content: str) -> str:
        """Clean and normalize extracted content"""
        
        if not content:
            return ""
        
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Remove common web artifacts
        content = re.sub(r'Cookie Policy|Privacy Policy|Terms of Service|Contact Us|About Us', '', content, flags=re.I)
        
        # Remove email patterns (optional)
        # content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', content)
        
        # Remove phone patterns (optional)
        # content = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '', content)
        
        # Clean up and return
        content = content.strip()
        return content
    
    async def _extract_links(self, soup: BeautifulSoup, current_url: str, base_domain: str, base_scheme: str) -> List[str]:
        """
        Extract all discoverable links from a page.
        """
        
        links = set()
        
        # Extract regular anchor links
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            absolute_url = urljoin(current_url, href)
            
            # Normalize URL
            parsed = urlparse(absolute_url)
            normalized_url = urlunparse((
                parsed.scheme or base_scheme,
                parsed.netloc or base_domain,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            
            # Only include same-domain links
            if urlparse(normalized_url).netloc == base_domain:
                links.add(normalized_url)
        
        # Extract links from JavaScript (basic pattern matching)
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for URL patterns in JavaScript
                url_patterns = re.findall(r'["\'](https?://[^"\']+)["\']', script.string)
                for url in url_patterns:
                    if urlparse(url).netloc == base_domain:
                        links.add(url)
        
        # Extract links from data attributes
        elements_with_data = soup.find_all(attrs={'data-url': True})
        for element in elements_with_data:
            url = element.get('data-url')
            if url:
                absolute_url = urljoin(current_url, url)
                if urlparse(absolute_url).netloc == base_domain:
                    links.add(absolute_url)
        
        # Extract links from iframe src attributes
        iframes = soup.find_all('iframe', src=True)
        for iframe in iframes:
            src = iframe.get('src')
            if src:
                absolute_url = urljoin(current_url, src)
                if urlparse(absolute_url).netloc == base_domain:
                    links.add(absolute_url)
        
        return list(links)
    
    def _should_crawl_url(self, url: str, exclude_patterns: List[str], include_patterns: List[str]) -> bool:
        """Determine if a URL should be crawled based on patterns"""
        
        # Check exclusion patterns
        for pattern in exclude_patterns:
            if pattern in url:
                return False
        
        # Check inclusion patterns (if specified)
        if include_patterns:
            for pattern in include_patterns:
                if pattern in url:
                    return True
            return False  # If include patterns specified but none match, exclude
        
        return True
    
    async def _parse_robots_txt(self, base_url: str) -> Dict[str, Any]:
        """Parse robots.txt file for crawling rules"""
        
        try:
            robots_url = urljoin(base_url, '/robots.txt')
            async with self.session.get(robots_url) as response:
                if response.status == 200:
                    content = await response.text()
                    return self._parse_robots_content(content)
        except Exception as e:
            self.logger.debug(f"Could not parse robots.txt: {e}")
        
        return {}
    
    def _parse_robots_content(self, content: str) -> Dict[str, Any]:
        """Parse robots.txt content"""
        
        rules = {'disallow': [], 'allow': [], 'crawl_delay': None}
        current_agent = '*'
        
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if ':' in line:
                directive, value = line.split(':', 1)
                directive = directive.strip().lower()
                value = value.strip()
                
                if directive == 'user-agent':
                    current_agent = value
                elif directive == 'disallow' and current_agent == '*':
                    if value:
                        rules['disallow'].append(value)
                elif directive == 'allow' and current_agent == '*':
                    if value:
                        rules['allow'].append(value)
                elif directive == 'crawl-delay' and current_agent == '*':
                    try:
                        rules['crawl_delay'] = float(value)
                    except ValueError:
                        pass
        
        return rules
    
    def _is_url_disallowed(self, url: str, robots_rules: Dict[str, Any]) -> bool:
        """Check if URL is disallowed by robots.txt rules"""
        
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        for disallow_path in robots_rules.get('disallow', []):
            if path.startswith(disallow_path):
                return True
        
        return False
    
    async def cancel_crawl(self, job_id: str) -> Dict[str, Any]:
        """
        Cancel a crawl job.
        Migrated from crawler_service.py
        """
        
        log_service_call(
            self.logger,
            "EnhancedCrawlerService",
            "cancel_crawl",
            job_id=job_id
        )
        
        try:
            # Update job status to cancelled
            await self._update_job_status(job_id, "cancelled")
            
            log_service_result(
                self.logger,
                "EnhancedCrawlerService",
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
                "EnhancedCrawlerService",
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
            # Split content into chunks using enhanced chunking
            chunks = self._enhanced_chunk_text(content)
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
    
    def _enhanced_chunk_text(self, text: str, chunk_size: int = 800, overlap: int = 100) -> List[str]:
        """
        Enhanced text chunking that respects sentence boundaries and semantic units.
        """
        
        if not text:
            return []
        
        # Split into sentences first
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # If adding this sentence would exceed chunk size
            if len(current_chunk) + len(sentence) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap from previous
                overlap_text = current_chunk[-overlap:] if overlap > 0 else ""
                current_chunk = overlap_text + " " + sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk if it exists
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Ensure minimum chunk size and merge small chunks
        final_chunks = []
        temp_chunk = ""
        
        for chunk in chunks:
            if len(chunk) < chunk_size // 2 and temp_chunk:
                temp_chunk += " " + chunk
            else:
                if temp_chunk:
                    final_chunks.append(temp_chunk)
                temp_chunk = chunk
        
        if temp_chunk:
            final_chunks.append(temp_chunk)
        
        return final_chunks
    
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
crawler_service = EnhancedCrawlerService()