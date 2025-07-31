from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance

client = QdrantClient(host="localhost", port=6333)

collection_name = "chatbot_embeddings"

# Create or recreate the collection
if client.collection_exists(collection_name):
    client.delete_collection(collection_name)
    print(f"Deleted existing collection `{collection_name}`")

client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
)
print(f"Created new collection `{collection_name}`")
