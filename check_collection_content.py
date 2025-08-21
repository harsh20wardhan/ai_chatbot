import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
import requests
import json

load_dotenv()

# Connect to Qdrant
qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
qdrant_api_key = os.environ.get("QDRANT_API_KEY", "")
client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

bot_id = "7644b70e-1c67-4df6-8518-af6fbe37a21e"

print(f"Checking collection: {bot_id}")

try:
    # Use direct HTTP request to avoid Pydantic validation issues
    headers = {}
    if qdrant_api_key:
        headers["api-key"] = qdrant_api_key
    
    response = requests.get(f"{qdrant_url}/collections/{bot_id}", headers=headers)
    
    if response.status_code == 200:
        collection_data = response.json()
        points_count = collection_data.get('result', {}).get('points_count', 0)
        print(f"Collection exists with {points_count} points")
        
        if points_count > 0:
            # Get some sample points using the client
            try:
                points = client.scroll(
                    collection_name=bot_id,
                    limit=5
                )[0]
                
                print(f"\nSample documents in collection:")
                for i, point in enumerate(points):
                    chunk = point.payload.get('chunk', 'No chunk data')[:200]
                    source = point.payload.get('source', 'No source')
                    print(f"\nDocument {i+1}:")
                    print(f"ID: {point.id}")
                    print(f"Source: {source}")
                    print(f"Content: {chunk}...")
                    print(f"Metadata keys: {list(point.payload.keys())}")
            except Exception as scroll_error:
                print(f"Error getting sample points: {scroll_error}")
        else:
            print("Collection is empty - no documents found!")
            print("\nThis means the RAG system has no knowledge base to search from.")
            print("You need to:")
            print("1. Check if documents were crawled and parsed")
            print("2. Verify the embedding service is working")
            print("3. Re-run the document ingestion process")
    else:
        print(f"Collection '{bot_id}' not found (HTTP {response.status_code})")
        
except Exception as e:
    print(f"Error: {e}")
    
try:
    # List all collections
    collections = client.get_collections()
    print(f"\nAvailable collections: {[c.name for c in collections.collections]}")
except Exception as e:
    print(f"Error listing collections: {e}")