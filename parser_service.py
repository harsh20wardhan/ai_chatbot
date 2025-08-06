from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import PyPDF2
import docx2txt
import json
import requests
import pg8000
import logging
import traceback
import uuid
import pandas as pd
import io
from pathlib import Path
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/parser.log')
    ]
)
logger = logging.getLogger('parser_service')

# Load environment variables
load_dotenv()

app = Flask(__name__)
API_KEY = os.environ.get("PARSER_SERVICE_KEY", "your-parser-secret-key")

# Initialize embedding model and Qdrant client
logger.info("Loading embedding model...")
embed_model = SentenceTransformer("hkunlp/instructor-xl")
logger.info("Embedding model loaded")

logger.info("Connecting to Qdrant...")
qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
qdrant_api_key = os.environ.get("QDRANT_API_KEY", "")
client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
logger.info(f"Connected to Qdrant at {qdrant_url}")

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

def parse_pdf(filepath):
    """Extract text from PDF using PyPDF2"""
    text = ""
    try:
        with open(filepath, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        logger.info(f"PDF parsed successfully: {filepath}, extracted {len(text)} characters")
    except Exception as e:
        logger.error(f"Error parsing PDF: {e}")
        logger.error(traceback.format_exc())
    return text

def parse_docx(filepath):
    """Extract text from DOCX using docx2txt"""
    try:
        text = docx2txt.process(filepath)
        logger.info(f"DOCX parsed successfully: {filepath}, extracted {len(text)} characters")
        return text
    except Exception as e:
        logger.error(f"Error parsing DOCX: {e}")
        logger.error(traceback.format_exc())
        return ""

def parse_txt(filepath):
    """Extract text from TXT file"""
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            text = file.read()
            logger.info(f"TXT parsed successfully: {filepath}, extracted {len(text)} characters")
            return text
    except Exception as e:
        logger.error(f"Error parsing TXT: {e}")
        logger.error(traceback.format_exc())
        return ""

def parse_excel(filepath):
    """Extract text from Excel files"""
    try:
        # Read all sheets
        excel_data = pd.read_excel(filepath, sheet_name=None)
        text_parts = []
        
        # Process each sheet
        for sheet_name, df in excel_data.items():
            text_parts.append(f"Sheet: {sheet_name}")
            
            # Convert headers and data to text
            headers = df.columns.tolist()
            text_parts.append(f"Headers: {', '.join(str(h) for h in headers)}")
            
            # Convert each row to text
            for idx, row in df.iterrows():
                row_text = []
                for col in headers:
                    value = row.get(col, '')
                    if pd.notna(value):  # Skip NaN values
                        row_text.append(f"{col}: {value}")
                text_parts.append("; ".join(row_text))
        
        text = "\n".join(text_parts)
        logger.info(f"Excel parsed successfully: {filepath}, extracted {len(text)} characters")
        return text
    except Exception as e:
        logger.error(f"Error parsing Excel: {e}")
        logger.error(traceback.format_exc())
        return ""

def chunk_text(text, chunk_size=500, overlap=50):
    """Split text into overlapping chunks"""
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if len(chunk) >= chunk_size // 2:  # Only keep chunks that are reasonably sized
            chunks.append(chunk)
    return chunks

def get_file_from_storage(supabase_url, supabase_key, bucket_name, file_path, local_path):
    """Download file from Supabase Storage"""
    try:
        # Construct the storage URL
        url = f"{supabase_url}/storage/v1/object/{bucket_name}/{file_path}"
        
        # Set up headers with Supabase key
        headers = {
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}"
        }
        
        # Make the request
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            # Ensure directory exists
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            # Write the file content to the local path
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"File downloaded successfully: {file_path} -> {local_path}")
            return True
        else:
            logger.error(f"Failed to download file: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        logger.error(traceback.format_exc())
        return False

def store_document_chunks(document_id, bot_id, user_id, chunks):
    """Store document chunks in the database"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Update document status to processing
            cur.execute("""
                UPDATE documents
                SET status = 'processing', updated_at = NOW()
                WHERE id = %s
            """, (document_id,))
            conn.commit()
            
            # Store chunks in database
            chunk_ids = []
            for i, chunk in enumerate(chunks):
                chunk_id = str(uuid.uuid4())
                cur.execute("""
                    INSERT INTO document_chunks (
                        id, document_id, bot_id, user_id, 
                        chunk_index, chunk_text, chunk_length
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    chunk_id,
                    document_id,
                    bot_id,
                    user_id,
                    i,
                    chunk,
                    len(chunk)
                ))
                result = cur.fetchone()
                if isinstance(result, tuple) and len(result) > 0:
                    chunk_ids.append(result[0])
                elif isinstance(result, list) and len(result) > 0:
                    chunk_ids.append(result[0])
                else:
                    chunk_ids.append(chunk_id)
            
            conn.commit()
            logger.info(f"Stored {len(chunks)} chunks for document {document_id}")
            return chunk_ids
    except Exception as e:
        logger.error(f"Error storing document chunks: {e}")
        logger.error(traceback.format_exc())
        conn.rollback()
        raise
    finally:
        if 'conn' in locals():
            conn.close()

def embed_and_store_chunks(document_id, bot_id, user_id, chunks, chunk_ids):
    """Embed chunks and store in Qdrant"""
    try:
        # Generate embeddings
        embeddings = embed_model.encode(chunks)
        logger.info(f"Generated {len(embeddings)} embeddings for document {document_id}")
        
        # Ensure collection exists
        try:
            collections = client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if bot_id not in collection_names:
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
                
                client.create_collection(
                    collection_name=bot_id,
                    vectors_config={"size": vector_size, "distance": "Cosine"}
                )
                logger.info(f"Created collection {bot_id}")
        except Exception as e:
            logger.error(f"Error checking/creating collection: {e}")
            logger.error(traceback.format_exc())
            raise
        
        # Prepare points for Qdrant
        points = []
        for i, (chunk, embedding, chunk_id) in enumerate(zip(chunks, embeddings, chunk_ids)):
            point_id = str(uuid.uuid4())
            points.append({
                "id": point_id,
                "vector": embedding.tolist(),
                "payload": {
                    "document_id": document_id,
                    "chunk_id": chunk_id,
                    "chunk_index": i,
                    "chunk": chunk,
                    "source_type": "document"
                }
            })
        
        # Upsert points to Qdrant
        client.upsert(
            collection_name=bot_id,
            points=points
        )
        logger.info(f"Upserted {len(points)} points to Qdrant collection {bot_id}")
        
        # Update document chunks with embedding information
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                for i, (point, chunk_id) in enumerate(zip(points, chunk_ids)):
                    cur.execute("""
                        UPDATE document_chunks
                        SET 
                            embedding_vector = %s,
                            qdrant_point_id = %s,
                            embedded_at = NOW()
                        WHERE id = %s
                    """, (
                        point["vector"],
                        point["id"],
                        chunk_id
                    ))
                conn.commit()
                logger.info(f"Updated {len(points)} chunks with embedding information")
        except Exception as e:
            logger.error(f"Error updating chunks with embedding info: {e}")
            logger.error(traceback.format_exc())
            conn.rollback()
            raise
        finally:
            if 'conn' in locals():
                conn.close()
        
        # Update document status to processed
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE documents
                    SET 
                        status = 'processed',
                        processed_at = NOW(),
                        updated_at = NOW()
                    WHERE id = %s
                """, (document_id,))
                conn.commit()
                logger.info(f"Updated document {document_id} status to processed")
        except Exception as e:
            logger.error(f"Error updating document status: {e}")
            logger.error(traceback.format_exc())
            conn.rollback()
            raise
        finally:
            if 'conn' in locals():
                conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error embedding and storing chunks: {e}")
        logger.error(traceback.format_exc())
        
        # Update document status to failed
        conn = get_db_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE documents
                    SET 
                        status = 'failed',
                        error = %s,
                        updated_at = NOW()
                    WHERE id = %s
                """, (str(e), document_id))
                conn.commit()
        except Exception as db_error:
            logger.error(f"Error updating document status to failed: {db_error}")
            conn.rollback()
        finally:
            if 'conn' in locals():
                conn.close()
        
        return False

@app.route("/parse", methods=["POST"])
def parse():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer ") or auth_header[7:] != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    document_id = data.get("document_id")
    file_path = data.get("file_path")
    file_type = data.get("file_type")
    bot_id = data.get("bot_id")
    
    logger.info(f"Processing document {document_id}, file type: {file_type}")
    
    # Get user_id from document
    user_id = None
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT user_id FROM documents WHERE id = %s", (document_id,))
            result = cur.fetchone()
            if result:
                if isinstance(result, tuple):
                    user_id = result[0]
                elif isinstance(result, list):
                    user_id = result[0]
                elif hasattr(result, 'get'):
                    user_id = result.get('user_id')
    except Exception as e:
        logger.error(f"Error fetching user_id: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Failed to fetch user_id: {str(e)}"}), 500
    finally:
        if 'conn' in locals():
            conn.close()
    
    if not user_id:
        logger.error(f"User ID not found for document {document_id}")
        return jsonify({"error": "User ID not found"}), 404
    
    # Download file from Supabase Storage
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    bucket_name = "documents"
    
    # Create a temporary local file path
    local_dir = "temp_files"
    os.makedirs(local_dir, exist_ok=True)
    local_path = os.path.join(local_dir, os.path.basename(file_path))
    
    if not get_file_from_storage(supabase_url, supabase_key, bucket_name, file_path, local_path):
        return jsonify({"error": "Failed to download file from storage"}), 500
    
    # Parse file based on type
    text = ""
    try:
        if file_type.lower() == "pdf":
            text = parse_pdf(local_path)
        elif file_type.lower() == "docx":
            text = parse_docx(local_path)
        elif file_type.lower() in ["txt", "md"]:
            text = parse_txt(local_path)
        elif file_type.lower() in ["xlsx", "xls"]:
            text = parse_excel(local_path)
        else:
            logger.error(f"Unsupported file type: {file_type}")
            return jsonify({"error": f"Unsupported file type: {file_type}"}), 400
        
        # Clean up the temporary file
        try:
            os.remove(local_path)
        except Exception as e:
            logger.warning(f"Failed to remove temporary file {local_path}: {e}")
        
        if not text:
            logger.error(f"No text extracted from document {document_id}")
            return jsonify({"error": "No text extracted from document"}), 400
        
        # Chunk the text
        chunks = chunk_text(text)
        logger.info(f"Document {document_id} split into {len(chunks)} chunks")
        
        # Store chunks in database
        try:
            chunk_ids = store_document_chunks(document_id, bot_id, user_id, chunks)
            
            # Embed and store chunks
            success = embed_and_store_chunks(document_id, bot_id, user_id, chunks, chunk_ids)
            
            if success:
                return jsonify({
                    "status": "processed", 
                    "document_id": document_id,
                    "bot_id": bot_id,
                    "chunks_count": len(chunks)
                })
            else:
                return jsonify({
                    "status": "failed",
                    "document_id": document_id,
                    "error": "Failed to embed and store chunks"
                }), 500
                
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            logger.error(traceback.format_exc())
            return jsonify({
                "status": "failed",
                "document_id": document_id,
                "error": str(e)
            }), 500
            
    except Exception as e:
        logger.error(f"Error parsing document {document_id}: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # Make sure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Make sure temp files directory exists
    os.makedirs('temp_files', exist_ok=True)
    
    logger.info(f"Starting parser service on port 8002...")
    app.run(host="0.0.0.0", port=8002) 