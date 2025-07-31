from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
import requests
import json
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)
API_KEY = os.environ.get("RAG_SERVICE_KEY", "your-rag-secret-key")

# Initialize embedding model and Qdrant client
print("Loading embedding model...")
embed_model = SentenceTransformer("hkunlp/instructor-xl")
print("Embedding model loaded")

print("Connecting to Qdrant...")
qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
qdrant_api_key = os.environ.get("QDRANT_API_KEY", "")
client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
print(f"Connected to Qdrant at {qdrant_url}")

# LLM settings
print("Configuring Ollama connection...")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "mistral:7b")
print(f"OLLAMA_URL: {OLLAMA_URL}")
print(f"OLLAMA_MODEL: {OLLAMA_MODEL}")

# Check if the model is available
try:
    base_url = OLLAMA_URL
    if base_url.endswith('/api/generate'):
        base_url = base_url[:-12]
    
    print(f"Checking if model {OLLAMA_MODEL} is available...")
    response = requests.get(f"{base_url}/api/tags", timeout=5)
    if response.status_code == 200:
        models = response.json().get('models', [])
        available_models = [m.get('name') for m in models if m.get('name')]
        print(f"Available models: {available_models}")
        
        if OLLAMA_MODEL not in available_models:
            print(f"⚠️ WARNING: Model '{OLLAMA_MODEL}' is not available in Ollama!")
            print(f"Please pull the model with: ollama pull {OLLAMA_MODEL}")
except Exception as e:
    print(f"Error checking model availability: {e}")

def format_chat_history(message_history):
    """Format message history for the prompt"""
    if not message_history:
        return ""
    
    formatted = "\n\nChat History:\n"
    for msg in message_history:
        role = "User" if msg["role"] == "user" else "Assistant"
        formatted += f"{role}: {msg['content']}\n"
    return formatted

@app.route("/chat", methods=["POST"])
def chat():
    print("\n[RAG] === Starting new chat request ===")
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer ") or auth_header[7:] != API_KEY:
        print("[RAG] Error: Unauthorized access")
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    query = data.get("query")
    bot_id = data.get("bot_id")
    conversation_id = data.get("conversation_id")
    message_history = data.get("message_history", [])
    
    print(f"[RAG] Processing chat query for bot {bot_id}, conversation {conversation_id}")
    print(f"[RAG] Query: '{query[:50]}...'")
    print(f"[RAG] Message history: {len(message_history)} messages")
    
    try:
        # 1. Embed user question
        print("[RAG] Embedding user query...")
        start_time = time.time()
        query_embedding = embed_model.encode([query])[0]
        print(f"[RAG] Query embedded in {time.time() - start_time:.2f} seconds")
        
        # 2. Search for relevant documents in Qdrant
        try:
            print(f"[RAG] Searching Qdrant collection '{bot_id}' for relevant documents...")
            start_time = time.time()
            search_results = client.search(
                collection_name=bot_id,
                query_vector=query_embedding.tolist(),
                limit=5
            )
            print(f"[RAG] Qdrant search completed in {time.time() - start_time:.2f} seconds")
            print(f"[RAG] Found {len(search_results)} relevant chunks")
            
            if not search_results:
                print("[RAG] Warning: No relevant documents found in vector database")
        except Exception as e:
            print(f"[RAG] Error searching Qdrant: {e}")
            search_results = []
        
        # 3. Extract context from search results
        context_chunks = []
        sources = []
        
        for i, hit in enumerate(search_results):
            context_chunks.append(hit.payload.get("chunk", ""))
            sources.append({
                "index": i,
                "score": hit.score,
                "text": hit.payload.get("chunk", "")[:100] + "...",
                "document_id": hit.payload.get("document_id", "unknown")
            })
        
        context = "\n\n".join(context_chunks)
        print(f"[RAG] Context assembled: {len(context)} characters")
        
        # 4. Include chat history if available
        chat_history = format_chat_history(message_history)
        print(f"[RAG] Chat history formatted: {len(chat_history)} characters")
        
        # 5. Build prompt with context and history
        prompt = f"""Answer the user's question based on the following context. If you cannot find the answer in the context, say that you don't know but provide your best guess based on general knowledge.

Context:
{context}
{chat_history}

User Question: {query}

Answer:"""
        print(f"[RAG] Prompt built: {len(prompt)} characters")
        
        # 6. Call LLM (Ollama)
        try:
            print(f"[RAG] Calling Ollama at {OLLAMA_URL} with model {OLLAMA_MODEL}...")
            start_time = time.time()
            
            # Check if Ollama is running first
            try:
                health_check = requests.get(OLLAMA_URL.replace('/api/generate', '/api/tags'), timeout=5)
                print(f"[RAG] Ollama health check status: {health_check.status_code}")
                if health_check.status_code == 200:
                    models = health_check.json().get('models', [])
                    print(f"[RAG] Available Ollama models: {[m.get('name') for m in models if m.get('name')]}")
                    if not any(m.get('name') == OLLAMA_MODEL for m in models):
                        print(f"[RAG] WARNING: Model {OLLAMA_MODEL} not found in available models")
            except requests.RequestException as e:
                print(f"[RAG] Ollama health check failed: {e}")
                print("[RAG] Is Ollama running? Please ensure it's started with: ollama serve")
            
            # Try to make the request with a timeout
            response = requests.post(
                OLLAMA_URL,
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
                timeout=60  # Increased timeout for Ollama generation
            )
            
            if response.status_code != 200:
                error_text = response.text
                print(f"[RAG] Error from Ollama: {response.status_code} {error_text}")
                
                # Provide a fallback response if Ollama is not available
                answer = "I'm sorry, I'm having trouble connecting to my language model right now. Please check that Ollama is running and try again."
                print(f"[RAG] Using fallback response")
                
                return jsonify({
                    "answer": answer,
                    "sources": sources,
                    "tokens_used": len(prompt.split()) + len(answer.split()),
                    "conversation_id": conversation_id,
                    "error": "LLM service unavailable"
                })
                
            answer = response.json().get("response", "").strip()
            print(f"[RAG] Ollama response received in {time.time() - start_time:.2f} seconds")
            print(f"[RAG] Generated answer ({len(answer)} chars): {answer[:100]}...")
        except Exception as e:
            print(f"[RAG] Error calling LLM: {e}")
            print(f"[RAG] Error type: {type(e).__name__}")
            import traceback
            print(f"[RAG] Traceback: {traceback.format_exc()}")
            
            # Provide a fallback response if there's an exception
            answer = "I'm sorry, I'm having trouble connecting to my language model right now. Please ensure Ollama is running with 'ollama serve' and has the requested model installed with 'ollama pull'."
            
            return jsonify({
                "answer": answer,
                "sources": sources,
                "tokens_used": len(prompt.split()) + len(answer.split()),
                "conversation_id": conversation_id,
                "error": f"Failed to call LLM: {str(e)}"
            })
        
        # 7. Return the answer with sources
        tokens_used = len(prompt.split()) + len(answer.split())
        print(f"[RAG] Tokens used: {tokens_used}")
        print(f"[RAG] Request completed successfully")
        
        return jsonify({
            "answer": answer,
            "sources": sources,
            "tokens_used": tokens_used,
            "conversation_id": conversation_id
        })
            
    except Exception as e:
        print(f"[RAG] Error in chat processing: {e}")
        return jsonify({"error": f"Failed to process chat request: {str(e)}"}), 500

if __name__ == "__main__":
    print(f"Starting RAG service on port 8004...")
    app.run(host="0.0.0.0", port=8004) 