from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

model = SentenceTransformer("hkunlp/instructor-xl")
client = QdrantClient(host="localhost", port=6333)
collection_name = "chatbot_embeddings"

question = "What is your return policy?"
query_vec = model.encode([question])[0]

# Use new query_points method replacing deprecated search
hits = client.query_points(
    collection_name=collection_name,
    query_vector=query_vec,
    limit=3
)

for hit in hits:
    print(f"Score: {hit.score}")
    print(f"Chunk: {hit.payload['chunk']}\n")
