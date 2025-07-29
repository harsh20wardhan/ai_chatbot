import requests
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient

ollama_model = "llama3"  # Or any model you have pulled with Ollama (check with: ollama list)
OLLAMA_URL = "http://localhost:11434/api/generate"

embed_model = SentenceTransformer("hkunlp/instructor-xl")
client = QdrantClient(host="localhost", port=6333)
collection_name = "chatbot_embeddings"

while True:
    question = input("\nEnter your question (or 'exit' to quit): ").strip()
    if question == "exit": break

    # 1. Embed user question
    q_vec = embed_model.encode([question])[0]

    # 2. Retrieve top chunks
    hits = client.search(collection_name, q_vec, limit=3)
    context_chunks = [h.payload["chunk"] for h in hits]

    # 3. Build Ollama prompt
    context = "\n\n".join(context_chunks)
    prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"

    # 4. Call Ollama's local LLM
    response = requests.post(
        OLLAMA_URL,
        json={"model": ollama_model, "prompt": prompt, "stream": False}
    )
    answer = response.json()["response"].strip()

    print("\nAnswer:", answer)
    print("\nContext sources returned:")
    for i, h in enumerate(hits, 1):
        print(f"{i}. [Score: {h.score:.3f}] {h.payload['chunk'][:80]}...")
