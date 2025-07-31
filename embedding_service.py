from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import uuid
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
API_KEY = os.environ.get("EMBEDDINGS_SERVICE_KEY", "your-embedding-secret-key")

# Initialize embedding model and Qdrant client
print("Loading embedding model...")
embed_model = SentenceTransformer("hkunlp/instructor-xl")
print("Embedding model loaded")

print("Connecting to Qdrant...")
qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
qdrant_api_key = os.environ.get("QDRANT_API_KEY", "")
client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
print(f"Connected to Qdrant at {qdrant_url}")

def chunk_text(text, chunk_size=500, overlap=50):
    """Split text into overlapping chunks"""
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        if len(chunk) >= chunk_size // 2:  # Only keep chunks that are reasonably sized
            chunks.append(chunk)
    return chunks

@app.route("/embed", methods=["POST"])
def embed():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer ") or auth_header[7:] != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    job_id = data.get("job_id")
    bot_id = data.get("bot_id")
    document_ids = data.get("document_ids", [])
    
    print(f"Processing embedding job {job_id} for bot {bot_id}, documents: {document_ids}")
    
    # In a real implementation, fetch the document content from database
    # For now, using dummy data
    for doc_id in document_ids:
        # This is where you'd fetch the actual document content from your database
        # For this example, we're using dummy text
        text = f"This is sample content for document {doc_id}. It would normally be fetched from the database."
        
        # Split text into chunks
        chunks = chunk_text(text)
        print(f"Document {doc_id}: split into {len(chunks)} chunks")
        
        # Embed chunks
        embeddings = embed_model.encode(chunks)
        print(f"Generated {len(embeddings)} embeddings")
        
        # Prepare points for Qdrant
        points = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())
            points.append({
                "id": point_id,
                "vector": embedding.tolist(),
                "payload": {
                    "document_id": doc_id,
                    "chunk_index": i,
                    "chunk": chunk,
                    "source_type": "document"
                }
            })
        
        # Ensure collection exists
        try:
            collections = client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if bot_id not in collection_names:
                client.create_collection(
                    collection_name=bot_id,
                    vectors_config={"size": len(embeddings[0]), "distance": "Cosine"}
                )
                print(f"Created collection {bot_id}")
        except Exception as e:
            print(f"Error checking/creating collection: {e}")
            return jsonify({"error": f"Failed to create collection: {str(e)}"}), 500
        
        # Upsert points
        try:
            client.upsert(
                collection_name=bot_id,
                points=points
            )
            print(f"Upserted {len(points)} points to collection {bot_id}")
        except Exception as e:
            print(f"Error upserting points: {e}")
            return jsonify({"error": f"Failed to upsert embeddings: {str(e)}"}), 500
    
    # In a real implementation, update the job status in the database
    
    return jsonify({
        "status": "completed", 
        "job_id": job_id,
        "documents_processed": len(document_ids)
    })

@app.route("/documents/<document_id>/delete", methods=["DELETE"])
def delete_document_embeddings(document_id):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer ") or auth_header[7:] != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    bot_id = data.get("bot_id")
    
    if not bot_id:
        return jsonify({"error": "Bot ID is required"}), 400
    
    try:
        # Delete embeddings for document from Qdrant
        # Using filter to delete only points with this document_id
        client.delete(
            collection_name=bot_id,
            points_selector={"filter": {"must": [{"key": "document_id", "match": {"value": document_id}}]}}
        )
        print(f"Deleted embeddings for document {document_id} from collection {bot_id}")
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error deleting embeddings: {e}")
        return jsonify({"error": f"Failed to delete embeddings: {str(e)}"}), 500

@app.route("/delete_all", methods=["POST"])
def delete_all_embeddings():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer ") or auth_header[7:] != API_KEY:
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    bot_id = data.get("bot_id")
    
    if not bot_id:
        return jsonify({"error": "Bot ID is required"}), 400
    
    try:
        # Delete the entire collection
        client.delete_collection(collection_name=bot_id)
        print(f"Deleted collection {bot_id}")
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error deleting collection: {e}")
        return jsonify({"error": f"Failed to delete collection: {str(e)}"}), 500

if __name__ == "__main__":
    print(f"Starting embedding service on port 8003...")
    app.run(host="0.0.0.0", port=8003) 