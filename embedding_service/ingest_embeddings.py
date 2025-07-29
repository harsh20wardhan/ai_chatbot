from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
import json

client = QdrantClient(host="localhost", port=6333)
collection_name = "chatbot_embeddings"

if not client.collection_exists(collection_name):
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=768, distance=Distance.COSINE),
    )
else:
    print(f"Collection '{collection_name}' already exists.")

with open("embeddings.json") as f:
    items = json.load(f)

points = []
for idx, item in enumerate(items):
    points.append({
        "id": idx,
        "vector": item["embedding"],
        "payload": {"chunk": item["chunk"], "source": "example_source"}
    })

client.upsert(collection_name=collection_name, points=points)
print("Embeddings uploaded to Qdrant!")
