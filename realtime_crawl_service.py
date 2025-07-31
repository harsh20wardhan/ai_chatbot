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
    return pg8000.connect(
        host=os.environ.get("SUPABASE_DB_HOST"),
        database=os.environ.get("SUPABASE_DB_NAME"),
        user=os.environ.get("SUPABASE_DB_USER"),
        password=os.environ.get("SUPABASE_DB_PASSWORD"),
        port=int(os.environ.get("SUPABASE_DB_PORT", "5432"))
    )

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
    print(f"[REALTIME_CRAWL] Starting crawl for {base_url} with max_pages={max_pages}")
    visited, to_visit = set(), [base_url]
    collected = []
    
    if exclude_patterns is None:
        exclude_patterns = []

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
            print(f"[REALTIME_CRAWL] Crawling: {url}")
            
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
                print(f"[REALTIME_CRAWL] Failed {url}: HTTP {resp.status_code}")
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
                print(f"[REALTIME_CRAWL] Skipping {url}: too little content")
                continue
            
            # Store in database
            conn = get_db_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO crawled_pages (id, crawl_job_id, bot_id, user_id, url, title, content, content_length, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        str(uuid.uuid4()),
                        job_id,
                        bot_id,
                        None,  # user_id will be set from crawl_job
                        url,
                        title_text,
                        text,
                        len(text),
                        'pending'
                    ))
                    page_id = cur.fetchone()['id']
                    conn.commit()
                    
                    # Emit page crawled event
                    if session_id:
                        socketio.emit('page_crawled', {
                            'page_id': str(page_id),
                            'url': url,
                            'title': title_text,
                            'content_length': len(text),
                            'pages_crawled': pages_crawled + 1
                        }, room=session_id)
                        
                        # Start embedding process for this page
                        threading.Thread(target=embed_page_realtime, args=(page_id, text, bot_id, session_id)).start()
                        
            except Exception as e:
                print(f"[REALTIME_CRAWL] Database error for {url}: {e}")
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
            
            print(f"[REALTIME_CRAWL] Successfully crawled: {url} ({len(text)} chars)")

            # Find new links
            for a in soup.find_all("a", href=True):
                next_url = urljoin(url, a['href'])
                if next_url not in visited and next_url not in to_visit:
                    to_visit.append(next_url)
                    
            visited.add(url)
            
        except Exception as e:
            print(f"[REALTIME_CRAWL] Failed {url}: {e}")
            if session_id:
                socketio.emit('crawl_error', {
                    'url': url,
                    'error': str(e)
                }, room=session_id)
    
    print(f"[REALTIME_CRAWL] Crawl completed. Total pages: {len(collected)}")
    
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
        print(f"[REALTIME_EMBED] Starting embedding for page {page_id}")
        
        if session_id:
            socketio.emit('embedding_started', {
                'page_id': str(page_id),
                'content_length': len(text)
            }, room=session_id)
        
        # Split text into chunks
        chunks = chunk_text(text)
        print(f"[REALTIME_EMBED] Split into {len(chunks)} chunks")
        
        if session_id:
            socketio.emit('embedding_progress', {
                'page_id': str(page_id),
                'chunks_count': len(chunks),
                'status': 'chunking_completed'
            }, room=session_id)
        
        # Generate embeddings
        embeddings = embed_model.encode(chunks)
        print(f"[REALTIME_EMBED] Generated {len(embeddings)} embeddings")
        
        if session_id:
            socketio.emit('embedding_progress', {
                'page_id': str(page_id),
                'embeddings_count': len(embeddings),
                'status': 'embeddings_generated'
            }, room=session_id)
        
        # Ensure collection exists
        try:
            collections = client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if bot_id not in collection_names:
                client.create_collection(
                    collection_name=bot_id,
                    vectors_config={"size": len(embeddings[0]), "distance": "Cosine"}
                )
                print(f"[REALTIME_EMBED] Created collection {bot_id}")
        except Exception as e:
            print(f"[REALTIME_EMBED] Error checking/creating collection: {e}")
            return
        
        # Store embeddings in database and Qdrant
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    qdrant_point_id = str(uuid.uuid4())
                    
                    # Store in database
                    cur.execute("""
                        INSERT INTO embedding_chunks (id, crawled_page_id, bot_id, user_id, chunk_index, chunk_text, chunk_length, embedding_vector, qdrant_point_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        str(uuid.uuid4()),
                        page_id,
                        bot_id,
                        None,  # user_id will be set from crawled_page
                        i,
                        chunk,
                        len(chunk),
                        embedding.tolist(),
                        qdrant_point_id
                    ))
                    
                    # Store in Qdrant
                    client.upsert(
                        collection_name=bot_id,
                        points=[{
                            "id": qdrant_point_id,
                            "vector": embedding.tolist(),
                            "payload": {
                                "page_id": str(page_id),
                                "chunk_index": i,
                                "chunk": chunk,
                                "source_type": "crawled_page"
                            }
                        }]
                    )
                    
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
                print(f"[REALTIME_EMBED] Successfully embedded page {page_id}")
                
                if session_id:
                    socketio.emit('embedding_completed', {
                        'page_id': str(page_id),
                        'chunks_stored': len(chunks),
                        'status': 'completed'
                    }, room=session_id)
                    
        except Exception as e:
            print(f"[REALTIME_EMBED] Error embedding page {page_id}: {e}")
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
        print(f"[REALTIME_EMBED] Unexpected error embedding page {page_id}: {e}")

@app.route("/realtime-crawl", methods=["POST"])
def start_realtime_crawl():
    """Start a realtime crawl with WebSocket updates"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer ") or auth_header[7:] != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    url = data.get("url")
    max_depth = data.get("max_depth", 3)
    exclude_patterns = data.get("exclude_patterns", [])
    bot_id = data.get("bot_id")
    job_id = data.get("job_id")
    
    if not url or not bot_id or not job_id:
        return jsonify({"error": "URL, bot_id, and job_id are required"}), 400
    
    print(f"[REALTIME_CRAWL] Starting realtime crawl for {url}")
    
    # Generate session ID for WebSocket communication
    session_id = str(uuid.uuid4())
    
    # Start crawling in background thread
    def crawl_thread():
        try:
            crawl_website_realtime(url, max_depth, exclude_patterns, session_id, bot_id, job_id)
        except Exception as e:
            print(f"[REALTIME_CRAWL] Crawl thread error: {e}")
            socketio.emit('crawl_error', {'error': str(e)}, room=session_id)
    
    threading.Thread(target=crawl_thread, daemon=True).start()
    
    return jsonify({
        "session_id": session_id,
        "status": "started",
        "url": url,
        "max_depth": max_depth
    })

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
            
            # Get recent pages
            cur.execute("""
                SELECT id, url, title, content_length, status, created_at
                FROM crawled_pages 
                WHERE crawl_job_id = %s 
                ORDER BY created_at DESC 
                LIMIT 10
            """, (job_id,))
            
            recent_pages = cur.fetchall()
            
            return jsonify({
                "job": dict(job),
                "recent_pages": [dict(page) for page in recent_pages]
            })
            
    except Exception as e:
        print(f"[REALTIME_CRAWL] Error getting status: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@socketio.on('connect')
def handle_connect():
    print(f"[WEBSOCKET] Client connected: {request.sid}")

@socketio.on('join')
def handle_join(data):
    session_id = data.get('session_id')
    if session_id:
        join_room(session_id)
        print(f"[WEBSOCKET] Client {request.sid} joined session {session_id}")
        emit('connected', {'session_id': session_id})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"[WEBSOCKET] Client disconnected: {request.sid}")

if __name__ == "__main__":
    print(f"Starting realtime crawl service on port 8005...")
    socketio.run(app, host="0.0.0.0", port=8005, debug=True) 