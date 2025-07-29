from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

def get_top_k_chunks(query, model, qdrant, collection_name, k=3):
    query_vec = model.encode([query])[0]
    hits = qdrant.query_points(
        collection_name=collection_name,
        query_vector=query_vec,
        limit=k
    )
    return [hit.payload['chunk'] for hit in hits], hits

def build_prompt(question, context_chunks):
    context = "\n\n".join(context_chunks)
    prompt = (
        f"Context:\n{context}\n\n"
        f"Question: {question}\n"
        f"Answer (be specific; cite context):"
    )
    return prompt

if __name__ == "__main__":
    # 1. Setup models, DB client
    embed_model = SentenceTransformer("hkunlp/instructor-xl")
    llm_name = "microsoft/phi-2"  # small, fast open LLM; change as needed
    tokenizer = AutoTokenizer.from_pretrained(llm_name)
    llm = AutoModelForCausalLM.from_pretrained(llm_name)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    llm = llm.to(device)

    qdrant = QdrantClient(host="localhost", port=6333)
    collection_name = "chatbot_embeddings"

    # 2. Get user question
    question = input("Your question: ")

    # 3. Retrieve relevant context from Qdrant
    context_chunks, hits = get_top_k_chunks(question, embed_model, qdrant, collection_name)

    # 4. Build LLM prompt
    prompt = build_prompt(question, context_chunks)
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    outputs = llm.generate(
        **inputs,
        max_new_tokens=128,
        do_sample=True,
        temperature=0.65,
        pad_token_id=tokenizer.eos_token_id,
    )
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True).split("Answer",1)[-1].strip()

    print("\n--- Answer ---\n", answer)
    print("\n--- Sources ---")
    for hit in hits:
        print(f"Score: {hit.score:.3f}, Source: {hit.payload.get('source','n/a')}")
