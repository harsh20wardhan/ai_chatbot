from flask import Flask, request, jsonify, Response, stream_template
from flask_socketio import SocketIO, emit, join_room, leave_room
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import uuid
import json
import time
import threading
from queue import Queue
import pg8000
import asyncio
import websockets
import logging
import traceback

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/realtime_crawl.log')
    ]
)
logger = logging.getLogger('realtime_crawl')

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("REALTIME_CRAWL_SECRET_KEY", "your-realtime-crawl-secret-key")
socketio = SocketIO(app, cors_allowed_origins="*")

API_KEY = os.environ.get("REALTIME_CRAWL_SERVICE_KEY", "your-realtime-crawl-secret-key")

# Initialize embedding model and Qdrant client
print("Loading embedding model...")
embed_model = SentenceTransformer("hkunlp/instructor-xl")
print("Embedding model loaded")

print("Connecting to Qdrant...")
qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
qdrant_api_key = os.environ.get("QDRANT_API_KEY", "")
client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
print(f"Connected to Qdrant at {qdrant_url}")

# Database connection
def get_db_connection():
    host = os.environ.get("SUPABASE_DB_HOST")
    database = os.environ.get("SUPABASE_DB_NAME")
    user = os.environ.get("SUPABASE_DB_USER")
    password = os.environ.get("SUPABASE_DB_PASSWORD")
    port = int(os.environ.get("SUPABASE_DB_PORT", "5432"))
    
    logger.debug(f"Connecting to database: host={host}, db={database}, user={user}, port={port}")
    
    try:
        conn = pg8000.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        logger.debug("Database connection successful")
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        logger.error(traceback.format_exc())
        raise

def chunk_text(text, chunk_size=500, overlap=50):
    """Split text into overlapping chunks"""
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if len(chunk) >= chunk_size // 2:  # Only keep chunks that are reasonably sized
            chunks.append(chunk)
    return chunks

def crawl_website_realtime(base_url, max_pages=20, exclude_patterns=None, session_id=None, bot_id=None, job_id=None):
    """Crawl website with realtime updates"""
    logger.info(f"Starting crawl for {base_url} with max_pages={max_pages}, bot_id={bot_id}, job_id={job_id}")
    visited, to_visit = set(), [base_url]
    collected = []
    
    if exclude_patterns is None:
        exclude_patterns = []
    
    # Update job status to 'running'
    if job_id:
        try:
            conn = get_db_connection()
            try:
                with conn.cursor() as cur:
                    logger.info(f"Updating job {job_id} status to running")
                    cur.execute("""
                        UPDATE crawl_jobs 
                        SET status = %s, 
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, ('running', job_id))
                    conn.commit()
                    logger.info(f"Successfully updated job {job_id} status to running")
            except Exception as e:
                logger.error(f"Failed to update job status to running: {e}")
                conn.rollback()
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Database connection error while updating job status to running: {e}")

    def is_same_domain(url):
        return urlparse(url).netloc == urlparse(base_url).netloc

    def should_exclude(url):
        return any(pattern in url for pattern in exclude_patterns)

    pages_crawled = 0
    total_content_length = 0

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited or not is_same_domain(url) or should_exclude(url):
            continue
        
        try:
            logger.info(f"Crawling: {url}")
            
            # Emit crawling status
            if session_id:
                socketio.emit('crawl_status', {
                    'status': 'crawling',
                    'url': url,
                    'pages_crawled': pages_crawled,
                    'total_pages': len(visited) + 1
                }, room=session_id)
            
            resp = requests.get(url, timeout=10)
            if resp.status_code != 200:
                logger.warning(f"Failed {url}: HTTP {resp.status_code}")
                continue
                
            soup = BeautifulSoup(resp.text, "html.parser")
            
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
                logger.info(f"Skipping {url}: too little content (only {len(text)} chars)")
                continue
            
            # Store in database
            logger.debug(f"Storing page in database: {url}, title={title_text}, content_length={len(text)}")
            conn = get_db_connection()
            try:
                with conn.cursor() as cur:
                    # First get the user_id from the crawl_job
                    logger.debug(f"Fetching user_id from crawl_job with job_id={job_id}")
                    cur.execute("SELECT user_id FROM crawl_jobs WHERE id = %s", (job_id,))
                    job_result = cur.fetchone()
                    logger.debug(f"Raw job_result: {job_result}, type: {type(job_result)}")
                    
                    if not job_result:
                        logger.error(f"No crawl_job found with id={job_id}")
                        raise Exception(f"No crawl_job found with id={job_id}")
                    
                    # Handle different result types from pg8000
                    if isinstance(job_result, tuple):
                        user_id = job_result[0]
                    elif isinstance(job_result, list):
                        user_id = job_result[0]
                    elif hasattr(job_result, 'get'):
                        user_id = job_result.get('user_id')
                    else:
                        logger.error(f"Unexpected job_result type: {type(job_result)}, value: {job_result}")
                        user_id = None
                    logger.debug(f"Found user_id={user_id} for job_id={job_id}")
                    
                    if not user_id:
                        logger.warning(f"user_id is null for job_id={job_id}, using a default test user")
                        user_id = "00000000-0000-0000-0000-000000000000"  # Default test user
                    
                    # Now insert with the user_id
                    logger.debug(f"Inserting page with user_id={user_id}")
                    cur.execute("""
                        INSERT INTO crawled_pages (id, crawl_job_id, bot_id, user_id, url, title, content, content_length, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        str(uuid.uuid4()),
                        job_id,
                        bot_id,
                        user_id,  # Now using the user_id from crawl_job
                        url,
                        title_text,
                        text,
                        len(text),
                        'pending'
                    ))
                    result = cur.fetchone()
                    logger.debug(f"Database insert result: {result}")
                    
                    # Handle different return types from pg8000
                    if isinstance(result, tuple):
                        page_id = result[0]  # First column is the ID
                    elif isinstance(result, list) and len(result) > 0:
                        page_id = result[0]  # First element of the list
                    elif hasattr(result, 'get'):
                        page_id = result.get('id')
                    else:
                        logger.error(f"Unexpected result type: {type(result)}, value: {result}")
                        page_id = str(uuid.uuid4())  # Fallback
                        
                    logger.debug(f"Extracted page_id: {page_id}")
                    conn.commit()
                    
                    logger.info(f"Successfully stored page in database with ID: {page_id}")
                    
                    # Emit page crawled event
                    if session_id:
                        socketio.emit('page_crawled', {
                            'page_id': str(page_id),
                            'url': url,
                            'title': title_text,
                            'content_length': len(text),
                            'pages_crawled': pages_crawled + 1
                        }, room=session_id)
                        
                        # Start embedding process for this page in background
                        threading.Thread(target=embed_page_realtime, args=(page_id, text, bot_id, session_id), daemon=True).start()
                        
            except Exception as e:
                logger.error(f"Database error for {url}: {e}")
                logger.error(traceback.format_exc())
                conn.rollback()
            finally:
                 if 'conn' in locals():
                    conn.close()
            
            collected.append({
                'url': url,
                'title': title_text,
                'content': text,
                'content_length': len(text)
            })
            
            pages_crawled += 1
            total_content_length += len(text)
            
            logger.info(f"Successfully crawled: {url} ({len(text)} chars)")
            
            # Update job progress periodically (every 5 pages or on the last page)
            if job_id and (pages_crawled % 5 == 0 or len(to_visit) == 0):
                try:
                    conn = get_db_connection()
                    try:
                        with conn.cursor() as cur:
                            cur.execute("""
                                UPDATE crawl_jobs 
                                SET pages_crawled = %s,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE id = %s
                            """, (pages_crawled, job_id))
                            conn.commit()
                            logger.debug(f"Updated job {job_id} progress: {pages_crawled} pages crawled")
                    except Exception as e:
                        logger.error(f"Failed to update job progress: {e}")
                        conn.rollback()
                    finally:
                        conn.close()
                except Exception as e:
                    logger.error(f"Database connection error while updating job progress: {e}")

            # Find new links
            for a in soup.find_all("a", href=True):
                next_url = urljoin(url, a['href'])
                if next_url not in visited and next_url not in to_visit:
                    to_visit.append(next_url)
                    
            visited.add(url)
            
        except Exception as e:
            logger.error(f"Failed {url}: {e}")
            logger.error(traceback.format_exc())
            if session_id:
                socketio.emit('crawl_error', {
                    'url': url,
                    'error': str(e)
                }, room=session_id)
    
    logger.info(f"Crawl completed. Total pages: {len(collected)}")
    
    # Update job status in database
    if job_id:
        try:
            conn = get_db_connection()
            try:
                with conn.cursor() as cur:
                    logger.info(f"Updating job {job_id} status to completed with {pages_crawled} pages")
                    cur.execute("""
                        UPDATE crawl_jobs 
                        SET status = %s, 
                            completed_at = CURRENT_TIMESTAMP,
                            updated_at = CURRENT_TIMESTAMP,
                            pages_crawled = %s
                        WHERE id = %s
                    """, ('completed', pages_crawled, job_id))
                    conn.commit()
                    logger.info(f"Successfully updated job {job_id} status to completed with {pages_crawled} pages")
            except Exception as e:
                logger.error(f"Failed to update job status: {e}")
                logger.error(traceback.format_exc())
                conn.rollback()
            finally:
                conn.close()
        except Exception as e:
            logger.error(f"Database connection error while updating job status: {e}")
    
    # Emit completion event
    if session_id:
        socketio.emit('crawl_completed', {
            'total_pages': len(collected),
            'total_content_length': total_content_length,
            'pages_crawled': pages_crawled
        }, room=session_id)
    
    return collected

def embed_page_realtime(page_id, text, bot_id, session_id=None):
    """Embed a single page in realtime"""
    try:
        logger.info(f"Starting embedding for page {page_id}, bot_id={bot_id}, text_length={len(text)}")
        
        if session_id:
            socketio.emit('embedding_started', {
                'page_id': str(page_id),
                'content_length': len(text)
            }, room=session_id)
        
        # Split text into chunks
        chunks = chunk_text(text)
        logger.info(f"Split into {len(chunks)} chunks")
        
        # Print first chunk for debugging
        if chunks:
            logger.debug(f"First chunk sample: {chunks[0][:100]}...")
        
        if session_id:
            socketio.emit('embedding_progress', {
                'page_id': str(page_id),
                'chunks_count': len(chunks),
                'status': 'chunking_completed'
            }, room=session_id)
        
        # Generate embeddings
        logger.info(f"Generating embeddings for {len(chunks)} chunks...")
        embeddings = embed_model.encode(chunks)
        logger.info(f"Generated {len(embeddings)} embeddings, first embedding shape: {embeddings[0].shape if len(embeddings) > 0 else 'N/A'}")
        
        if session_id:
            socketio.emit('embedding_progress', {
                'page_id': str(page_id),
                'embeddings_count': len(embeddings),
                'status': 'embeddings_generated'
            }, room=session_id)
        
        # Ensure collection exists
        try:
            logger.info(f"Checking if Qdrant collection exists for bot_id: {bot_id}")
            collections = client.get_collections()
            collection_names = [c.name for c in collections.collections]
            logger.debug(f"Existing collections: {collection_names}")
            
            if bot_id not in collection_names:
                logger.info(f"Collection {bot_id} does not exist, creating it now")
                # Handle both list and numpy array types
                try:
                    if len(embeddings) > 0:
                        vector_size = len(embeddings[0])
                        logger.debug(f"Detected vector size: {vector_size}")
                    else:
                        vector_size = 768  # Default size
                        logger.debug(f"Using default vector size: {vector_size}")
                except (TypeError, ValueError):
                    vector_size = 768  # Default size
                    logger.debug(f"Error detecting vector size, using default: {vector_size}")
                logger.debug(f"Creating collection with vector size: {vector_size}")
                
                client.create_collection(
                    collection_name=bot_id,
                    vectors_config={"size": vector_size, "distance": "Cosine"}
                )
                logger.info(f"Successfully created collection {bot_id}")
            else:
                logger.info(f"Collection {bot_id} already exists")
                
            # Verify collection was created/exists
            collections_after = client.get_collections()
            collection_names_after = [c.name for c in collections_after.collections]
            if bot_id in collection_names_after:
                logger.info(f"Verified collection {bot_id} exists")
            else:
                logger.error(f"Failed to create or find collection {bot_id}")
                raise Exception(f"Collection {bot_id} not found after creation attempt")
                
        except Exception as e:
            logger.error(f"Error checking/creating collection: {e}")
            logger.error(traceback.format_exc())
            return
        
        # Store embeddings in database and Qdrant
        logger.info(f"Storing {len(chunks)} embeddings in database and Qdrant for page {page_id}")
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                # First get the user_id from the crawled_page
                logger.debug(f"Fetching user_id from crawled_page with page_id={page_id}")
                cur.execute("SELECT user_id FROM crawled_pages WHERE id = %s", (page_id,))
                page_result = cur.fetchone()
                logger.debug(f"Raw page_result: {page_result}, type: {type(page_result)}")
                
                if not page_result:
                    logger.error(f"No crawled_page found with id={page_id}")
                    raise Exception(f"No crawled_page found with id={page_id}")
                
                # Handle different result types from pg8000
                if isinstance(page_result, tuple):
                    user_id = page_result[0]
                elif isinstance(page_result, list):
                    user_id = page_result[0]
                elif hasattr(page_result, 'get'):
                    user_id = page_result.get('user_id')
                else:
                    logger.error(f"Unexpected page_result type: {type(page_result)}, value: {page_result}")
                    user_id = None
                logger.debug(f"Found user_id={user_id} for page_id={page_id}")
                
                if not user_id:
                    logger.warning(f"user_id is null for page_id={page_id}, using a default test user")
                    user_id = "00000000-0000-0000-0000-000000000000"  # Default test user
                
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    qdrant_point_id = str(uuid.uuid4())
                    chunk_id = str(uuid.uuid4())
                    
                    # Log the chunk details for debugging
                    if i == 0 or i % 10 == 0:
                        logger.debug(f"Processing chunk {i+1}/{len(chunks)}: length={len(chunk)}, first 50 chars: {chunk[:50]}...")
                    
                    # Store in database
                    try:
                        logger.debug(f"Inserting chunk {i+1} into embedding_chunks table with user_id={user_id}")
                        cur.execute("""
                            INSERT INTO embedding_chunks (id, crawled_page_id, bot_id, user_id, chunk_index, chunk_text, chunk_length, embedding_vector, qdrant_point_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            chunk_id,
                            page_id,
                            bot_id,
                            user_id,  # Now using the user_id from crawled_page
                            i,
                            chunk,
                            len(chunk),
                            embedding.tolist(),
                            qdrant_point_id
                        ))
                        logger.debug(f"Successfully inserted chunk {i+1} with ID {chunk_id}")
                    except Exception as e:
                        logger.error(f"Error inserting chunk {i+1}: {e}")
                        logger.error(f"Chunk data: id={chunk_id}, page_id={page_id}, bot_id={bot_id}, index={i}, length={len(chunk)}")
                        raise
                    
                    # Store in Qdrant
                    logger.debug(f"Upserting chunk {i+1}/{len(chunks)} to Qdrant, point_id={qdrant_point_id}")
                    try:
                        # Prepare the point data
                        point_data = {
                            "id": qdrant_point_id,
                            "vector": embedding.tolist(),
                            "payload": {
                                "page_id": str(page_id),
                                "chunk_index": i,
                                "chunk": chunk,
                                "source_type": "crawled_page"
                            }
                        }
                        
                        if i == 0:
                            logger.debug(f"Sample vector dimensions: {len(embedding.tolist())}")
                            logger.debug(f"Sample payload: {point_data['payload']}")
                        
                        # Upsert to Qdrant
                        client.upsert(
                            collection_name=bot_id,
                            points=[point_data]
                        )
                        logger.debug(f"Successfully upserted chunk {i+1} to Qdrant")
                    except Exception as e:
                        logger.error(f"Error upserting to Qdrant: {e}")
                        logger.error(traceback.format_exc())
                        raise
                    
                    if session_id and i % 5 == 0:  # Emit progress every 5 chunks
                        socketio.emit('embedding_progress', {
                            'page_id': str(page_id),
                            'chunks_processed': i + 1,
                            'total_chunks': len(chunks),
                            'status': 'storing_chunks'
                        }, room=session_id)
                
                # Update page status
                cur.execute("""
                    UPDATE crawled_pages 
                    SET status = 'embedded', embedded_at = NOW() 
                    WHERE id = %s
                """, (page_id,))
                
                conn.commit()
                logger.info(f"Successfully embedded page {page_id} with {len(chunks)} chunks")
                
                if session_id:
                    socketio.emit('embedding_completed', {
                        'page_id': str(page_id),
                        'chunks_stored': len(chunks),
                        'status': 'completed'
                    }, room=session_id)
                    
        except Exception as e:
            logger.error(f"Error embedding page {page_id}: {e}")
            logger.error(traceback.format_exc())
            conn.rollback()
            
            # Update page status to failed
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE crawled_pages 
                        SET status = 'failed', error = %s 
                        WHERE id = %s
                    """, (str(e), page_id))
                    conn.commit()
            except:
                pass
                
            if session_id:
                socketio.emit('embedding_error', {
                    'page_id': str(page_id),
                    'error': str(e)
                }, room=session_id)
        finally:
            conn.close()
            
    except Exception as e:
        logger.error(f"Unexpected error embedding page {page_id}: {e}")
        logger.error(traceback.format_exc())

@app.route("/realtime-crawl", methods=["POST"])
def start_realtime_crawl():
    """Start a realtime crawl with WebSocket updates"""
    # For debugging, log all request headers and body
    logger.debug(f"Request headers: {dict(request.headers)}")
    logger.debug(f"Request body: {request.json}")
    
    # Temporarily bypass authentication for testing
    # auth_header = request.headers.get("Authorization")
    # if not auth_header or not auth_header.startswith("Bearer ") or auth_header[7:] != API_KEY:
    #     return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    url = data.get("url")
    max_depth = data.get("max_depth", 3)
    exclude_patterns = data.get("exclude_patterns", [])
    bot_id = data.get("bot_id")
    job_id = data.get("job_id")
    
    logger.info(f"Received crawl request: url={url}, max_depth={max_depth}, bot_id={bot_id}, job_id={job_id}")
    
    if not url or not bot_id or not job_id:
        logger.error(f"Missing required parameters: url={url}, bot_id={bot_id}, job_id={job_id}")
        return jsonify({"error": "URL, bot_id, and job_id are required"}), 400
    
    # Test database connection before starting crawl
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check if job exists
            cur.execute("SELECT id, status FROM crawl_jobs WHERE id = %s", (job_id,))
            job = cur.fetchone()
            if job:
                logger.info(f"Found existing job in database: {job}")
            else:
                logger.warning(f"Job {job_id} not found in database")
        conn.close()
    except Exception as e:
        logger.error(f"Database check failed before crawl: {e}")
        logger.error(traceback.format_exc())
        # Continue anyway for testing
    
    # Generate session ID for WebSocket communication
    session_id = str(uuid.uuid4())
    logger.info(f"Generated WebSocket session ID: {session_id}")
    
    # Start crawling in background thread
    def crawl_thread():
        try:
            logger.info(f"Starting crawl thread for job {job_id}, URL {url}")
            crawl_website_realtime(url, max_depth, exclude_patterns, session_id, bot_id, job_id)
            logger.info(f"Crawl thread completed for job {job_id}")
        except Exception as e:
            logger.error(f"Crawl thread error: {e}")
            logger.error(traceback.format_exc())
            
            # Update job status to failed
            try:
                conn = get_db_connection()
                try:
                    with conn.cursor() as cur:
                        logger.info(f"Updating job {job_id} status to failed due to error: {str(e)}")
                        cur.execute("""
                            UPDATE crawl_jobs 
                            SET status = %s, 
                                completed_at = CURRENT_TIMESTAMP,
                                updated_at = CURRENT_TIMESTAMP,
                                error = %s
                            WHERE id = %s
                        """, ('failed', str(e), job_id))
                        conn.commit()
                        logger.info(f"Successfully updated job {job_id} status to failed")
                except Exception as db_e:
                    logger.error(f"Failed to update job status to failed: {db_e}")
                    conn.rollback()
                finally:
                    conn.close()
            except Exception as db_e:
                logger.error(f"Database connection error while updating job status to failed: {db_e}")
            
            socketio.emit('crawl_error', {'error': str(e)}, room=session_id)
    
    logger.info(f"Starting crawl thread for {url}")
    threading.Thread(target=crawl_thread, daemon=True).start()
    
    return jsonify({
        "session_id": session_id,
        "status": "started",
        "url": url,
        "max_depth": max_depth,
        "bot_id": bot_id,
        "job_id": job_id
    })

@app.route("/debug/db-connection", methods=["GET"])
def test_db_connection():
    """Test database connection and return status"""
    try:
        logger.info("Testing database connection...")
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1 as test")
            result = cur.fetchone()
            logger.info(f"Database connection test result: {result}")
            
            # Test querying the crawl_jobs table
            cur.execute("SELECT COUNT(*) FROM crawl_jobs")
            count = cur.fetchone()
            logger.info(f"Number of crawl jobs: {count}")
            
            # Test querying the crawled_pages table
            cur.execute("SELECT COUNT(*) FROM crawled_pages")
            pages_count = cur.fetchone()
            logger.info(f"Number of crawled pages: {pages_count}")
            
            # Get database tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = [table[0] for table in cur.fetchall()]
            logger.info(f"Database tables: {tables}")
            
        conn.close()
        return jsonify({
            "status": "success",
            "message": "Database connection successful",
            "crawl_jobs_count": count[0] if isinstance(count, tuple) else count,
            "crawled_pages_count": pages_count[0] if isinstance(pages_count, tuple) else pages_count,
            "tables": tables
        })
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "message": f"Database connection failed: {str(e)}"
        }), 500

@app.route("/debug/direct-crawl", methods=["POST"])
def test_direct_crawl():
    """Test crawling directly without going through the API"""
    try:
        data = request.json
        url = data.get("url", "https://webscraper.io/test-sites/e-commerce/allinone")
        max_depth = data.get("max_depth", 2)
        bot_id = data.get("bot_id", "test-bot-" + str(uuid.uuid4()))
        
        logger.info(f"Starting direct test crawl for URL: {url}, max_depth: {max_depth}, bot_id: {bot_id}")
        
        # Generate test job_id
        job_id = str(uuid.uuid4())
        logger.info(f"Generated test job_id: {job_id}")
        
        # Generate session ID for WebSocket communication
        session_id = str(uuid.uuid4())
        logger.info(f"Generated test session_id: {session_id}")
        
        # Start crawling in background thread
        def crawl_thread():
            try:
                logger.info(f"Starting direct test crawl thread")
                results = crawl_website_realtime(url, max_depth, [], session_id, bot_id, job_id)
                logger.info(f"Direct test crawl completed, pages crawled: {len(results) if results else 0}")
            except Exception as e:
                logger.error(f"Direct test crawl error: {e}")
                logger.error(traceback.format_exc())
        
        threading.Thread(target=crawl_thread, daemon=True).start()
        
        return jsonify({
            "status": "started",
            "message": "Direct test crawl started",
            "url": url,
            "max_depth": max_depth,
            "bot_id": bot_id,
            "job_id": job_id,
            "session_id": session_id
        })
    except Exception as e:
        logger.error(f"Error starting direct test crawl: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "message": f"Error starting direct test crawl: {str(e)}"
        }), 500

@app.route("/debug/qdrant-connection", methods=["GET"])
def test_qdrant_connection():
    """Test Qdrant connection and return status"""
    try:
        logger.info("Testing Qdrant connection...")
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        return jsonify({
            "status": "success",
            "message": "Qdrant connection successful",
            "collections": collection_names,
            "qdrant_url": qdrant_url
        })
    except Exception as e:
        logger.error(f"Qdrant connection test failed: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "status": "error",
            "message": f"Qdrant connection failed: {str(e)}"
        }), 500

@app.route("/crawl-status/<job_id>", methods=["GET"])
def get_crawl_status(job_id):
    """Get the status of a crawl job"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer ") or auth_header[7:] != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
    
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Get crawl job info
            cur.execute("""
                SELECT cj.*, 
                       COUNT(cp.id) as pages_crawled,
                       COUNT(CASE WHEN cp.status = 'embedded' THEN 1 END) as pages_embedded,
                       COUNT(CASE WHEN cp.status = 'failed' THEN 1 END) as pages_failed
                FROM crawl_jobs cj
                LEFT JOIN crawled_pages cp ON cj.id = cp.crawl_job_id
                WHERE cj.id = %s
                GROUP BY cj.id
            """, (job_id,))
            
            job = cur.fetchone()
            if not job:
                return jsonify({"error": "Crawl job not found"}), 404
            
            # Log the job data for debugging
            logger.debug(f"Job data: {job}")
            
            # Convert tuple to dict for pg8000
            job_dict = {}
            if isinstance(job, tuple):
                columns = [desc[0] for desc in cur.description]
                job_dict = dict(zip(columns, job))
            else:
                job_dict = dict(job)
            
            # Get recent pages
            cur.execute("""
                SELECT id, url, title, content_length, status, created_at
                FROM crawled_pages 
                WHERE crawl_job_id = %s 
                ORDER BY created_at DESC 
                LIMIT 10
            """, (job_id,))
            
            recent_pages = cur.fetchall()
            logger.debug(f"Recent pages count: {len(recent_pages)}")
            
            # Convert tuples to dicts for pg8000
            pages_list = []
            if recent_pages and isinstance(recent_pages[0], tuple):
                columns = [desc[0] for desc in cur.description]
                for page in recent_pages:
                    pages_list.append(dict(zip(columns, page)))
            else:
                pages_list = [dict(page) for page in recent_pages]
            
            return jsonify({
                "job": job_dict,
                "recent_pages": pages_list
            })
            
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@socketio.on('connect')
def handle_connect():
    logger.info(f"WebSocket client connected: {request.sid}")

@socketio.on('join')
def handle_join(data):
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        logger.info(f"WebSocket client {request.sid} joined session {session_id}")
        emit('connected', {'session_id': session_id})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"WebSocket client disconnected: {request.sid}")

if __name__ == "__main__":
    # Make sure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    logger.info(f"Starting realtime crawl service on port 8005...")
    logger.info(f"Environment variables loaded: QDRANT_URL={qdrant_url}, SUPABASE_DB_HOST={os.environ.get('SUPABASE_DB_HOST')}")
    socketio.run(app, host="0.0.0.0", port=8005, debug=True) 