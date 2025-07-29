# embedding/embedding_service.py

from sentence_transformers import SentenceTransformer
from nltk.tokenize import sent_tokenize
import numpy as np
import sys, json

model = SentenceTransformer("hkunlp/instructor-xl")  # Or a smaller model if no GPU

def chunk_text(text, max_sentences=5):
    sentences = sent_tokenize(text)
    chunks = []
    for i in range(0, len(sentences), max_sentences):
        chunk = ' '.join(sentences[i:i + max_sentences])
        chunks.append(chunk)
    return chunks

if __name__ == "__main__":
    text = sys.stdin.read()
    chunks = chunk_text(text)
    embeddings = model.encode(chunks)
    result = [{"chunk": chunk, "embedding": emb.tolist()} for chunk, emb in zip(chunks, embeddings)]
    print(json.dumps(result))
