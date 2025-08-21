import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Connect to Qdrant
client = QdrantClient(
    url=os.getenv('QDRANT_URL'),
    api_key=os.getenv('QDRANT_API_KEY')
)

bot_id = "7644b70e-1c67-4df6-8518-af6fbe37a21e"

# Delete old collection
try:
    client.delete_collection(collection_name=bot_id)
    print(f"Deleted old collection {bot_id}")
except:
    print("Collection doesn't exist or already deleted")

# Create new collection with correct dimensions
client.create_collection(
    collection_name=bot_id,
    vectors_config=VectorParams(size=1024, distance=Distance.COSINE)
)
print(f"Created new collection {bot_id} with 1024 dimensions")