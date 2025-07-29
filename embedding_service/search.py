from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

model = SentenceTransformer("hkunlp/instructor-xl")
client = QdrantClient(host="localhost", port=6333)
collection_name = "chatbot_embeddings"

# Prompt user for their question via terminal/CLI
question = input("Enter your question: ")
query_vec = model.encode([question])[0]

hits = client.search(collection_name, query_vec, limit=3)

for hit in hits:
    print(f"Score: {hit.score}")
    print(f"Chunk: {hit.payload['chunk']}\n")
