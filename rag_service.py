# Replace the current logging setup at the top
import logging
import sys
from datetime import datetime

# Configure proper logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - [RAG] - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/rag_debug.log')
    ]
)
logger = logging.getLogger(__name__)
from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import boto3
from qdrant_client import QdrantClient
import json
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)
API_KEY = os.environ.get("RAG_SERVICE_KEY", "your-rag-secret-key")

# Initialize embedding model and Qdrant client
# Bedrock client setup
bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name=os.environ.get("AWS_REGION"))

# Bedrock embedding model
embedding_model_id = "amazon.titan-embed-text-v2:0"
print("Bedrock embedding model configured.")

print("Connecting to Qdrant...")
qdrant_url = os.environ.get("QDRANT_URL", "http://localhost:6333")
qdrant_api_key = os.environ.get("QDRANT_API_KEY", "")
client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
print(f"Connected to Qdrant at {qdrant_url}")

# LLM settings
# Bedrock LLM model
llm_model_id = "openai.gpt-oss-20b-1:0" # Or any other model available in Bedrock
print("Bedrock LLM model configured.")

def format_chat_history(message_history):
    """Format message history for the prompt"""
    if not message_history:
        return ""
    
    formatted = "\n\nChat History:\n"
    for msg in message_history:
        role = "User" if msg["role"] == "user" else "Assistant"
        formatted += f"{role}: {msg['content']}\n"
    return formatted

# Add filtering function to remove hidden/thinking-style tags
def filter_ai_response(content):
    """Remove hidden meta-thinking blocks and similar tags from AI responses.

    Strips blocks like <thinking>...</thinking>, <reasoning>...</reasoning>,
    <reflection>...</reflection>, <tool_call>...</tool_call>, etc.
    """
    if not content or not isinstance(content, str):
        return content

    import re

    # Tags to strip completely (case-insensitive)
    removable_tags = [
        'thinking', 'reasoning', 'reflection', 'tool_call', 'tool_output',
        'analysis', 'chain_of_thought', 'cot', 'scratchpad'
    ]

    for tag in removable_tags:
        pattern = rf'<{tag}[^>]*>[\s\S]*?</{tag}>'
        content = re.sub(pattern, '', content, flags=re.IGNORECASE)

    # Also remove accidental self-closing variants like <thinking/> (rare)
    content = re.sub(r'<(?:' + '|'.join(removable_tags) + r')(?:\s[^>]*)?\s*/>', '', content, flags=re.IGNORECASE)

    # Normalize excess blank lines
    content = re.sub(r'\n\s*\n', '\n', content)

    return content.strip()

# In the chat function, replace print statements with logger calls:
@app.route("/chat", methods=["POST"])
def chat():
    logger.info("=== Starting new chat request ===")
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer ") or auth_header[7:] != API_KEY:
        print("[RAG] Error: Unauthorized access")
        return jsonify({"error": "Unauthorized"}), 401
        
    data = request.json
    query = data.get("query")
    bot_id = data.get("bot_id")
    conversation_id = data.get("conversation_id")
    message_history = data.get("message_history", [])
    
    # Replace all print(f"[RAG] ...") with logger.info(...)
    logger.info(f"Processing chat query for bot {bot_id}, conversation {conversation_id}")
    logger.info(f"Query: '{query[:50]}...'")
    logger.info(f"Message history: {len(message_history)} messages")
    
    try:
        # 1. Embed user question
        print("[RAG] Embedding user query...")
        start_time = time.time()
        response = bedrock_runtime.invoke_model(
            body=json.dumps({"inputText": query}),
            modelId=embedding_model_id,
            accept="application/json",
            contentType="application/json"
        )
        response_body = json.loads(response.get("body").read())
        query_embedding = response_body.get("embedding")
        print(f"[RAG] Query embedded in {time.time() - start_time:.2f} seconds")
        
        # 2. Search for relevant documents in Qdrant
        search_results = []
        try:
            logger.info(f"Searching Qdrant collection '{bot_id}' for relevant documents...")
            logger.info(f"Query embedding length: {len(query_embedding) if query_embedding else 'None'}")
            
            # Check available collections
            collections = client.get_collections()
            collection_names = [c.name for c in collections.collections]
            logger.info(f"Available collections: {collection_names}")
            
            if bot_id not in collection_names:
                logger.error(f"Collection '{bot_id}' does not exist!")
                logger.error(f"Available collections: {collection_names}")
                search_results = []
            else:
                # Collection exists, get info and search
                try:
                    collection_info = client.get_collection(bot_id)
                    logger.info(f"Collection '{bot_id}' has {collection_info.points_count} points")
                    
                    if collection_info.points_count == 0:
                        logger.warning(f"Collection '{bot_id}' exists but has no documents!")
                        search_results = []
                    else:
                        # Perform the search
                        start_time = time.time()
                        search_results = client.search(
                            collection_name=bot_id,
                            query_vector=query_embedding,
                            limit=5
                        )
                        logger.info(f"Qdrant search completed in {time.time() - start_time:.2f} seconds")
                        logger.info(f"Found {len(search_results)} relevant chunks")
                        
                        if search_results:
                            logger.info(f"First result score: {search_results[0].score}")
                            logger.info(f"First result preview: {search_results[0].payload.get('chunk', '')[:100]}...")
                        else:
                            logger.warning("Search returned no results - check embedding similarity")
                            
                except Exception as collection_error:
                    logger.error(f"Error accessing collection info: {collection_error}")
                    # Try direct search anyway
                    try:
                        search_results = client.search(
                            collection_name=bot_id,
                            query_vector=query_embedding,
                            limit=5
                        )
                        logger.info(f"Direct search found {len(search_results)} results")
                    except Exception as search_error:
                        logger.error(f"Direct search also failed: {search_error}")
                        search_results = []
                        
        except Exception as e:
            logger.error(f"Error in Qdrant operations: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            search_results = []
            
        if not search_results:
            print("[RAG] Warning: No relevant documents found in vector database")

        # Continue with context assembly...
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
        
        # 6. Call LLM (Bedrock)
        try:
            print(f"[RAG] Calling Bedrock with model {llm_model_id}...")
            start_time = time.time()

            body = json.dumps({
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                "max_completion_tokens": 2000,
                "temperature": 0.7,
                "top_p": 0.9
            })

            response = bedrock_runtime.invoke_model(
                body=body,
                modelId=llm_model_id,
                accept="application/json",
                contentType="application/json"
            )

            response_body = json.loads(response.get("body").read())
            # OpenAI-compatible OSS models return choices[0].message.content
            answer = response_body.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

            print(f"[RAG] Bedrock response received in {time.time() - start_time:.2f} seconds")
            print(f"[RAG] Generated answer ({len(answer)} chars): {answer[:100]}...")
        except Exception as e:
            logging.exception("Error invoking LLM:")
            answer = "I'm sorry, I'm having trouble connecting to my language model right now. Please check your AWS Bedrock configuration."
            filtered_answer = filter_ai_response(answer)

            # Build HTML and plain-text variants for frontend consumption
            try:
                import markdown as md
                html_answer = md.markdown(
                    filtered_answer,
                    extensions=["fenced_code", "tables", "nl2br"]
                )
            except Exception:
                import html as _html
                html_answer = "<p>" + _html.escape(filtered_answer).replace("\n", "<br>") + "</p>"

            # Sanitize HTML if bleach is available
            try:
                import bleach
                allowed_tags = [
                    'p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'blockquote',
                    'code', 'pre', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table',
                    'thead', 'tbody', 'tr', 'th', 'td'
                ]
                allowed_attrs = {
                    'a': ['href', 'title', 'target', 'rel'],
                    'code': ['class']
                }
                html_answer = bleach.clean(html_answer, tags=allowed_tags, attributes=allowed_attrs, strip=True)
            except Exception:
                pass

            # Derive plain text
            try:
                from bs4 import BeautifulSoup
                answer_text = BeautifulSoup(html_answer, "html.parser").get_text("\n")
            except Exception:
                import re as _re
                answer_text = _re.sub(r"<[^>]+>", "", html_answer)

            return jsonify({
                "answer": answer_text,  # processed plain text
                "answer_text": answer_text,
                "answer_html": html_answer,
                "sources": sources,
                "tokens_used": len(prompt.split()) + len(answer.split()),
                "conversation_id": conversation_id,
                "error": f"Failed to call LLM: {str(e)}"
            })
        
        # 7. Return the answer with sources
        tokens_used = len(prompt.split()) + len(answer.split())
        print(f"[RAG] Tokens used: {tokens_used}")
        print(f"[RAG] Request completed successfully")
        
        # Filter the answer to remove thinking and reasoning tags
        filtered_answer = filter_ai_response(answer)

        # Build HTML and plain-text variants for frontend consumption
        try:
            import markdown as md
            html_answer = md.markdown(
                filtered_answer,
                extensions=["fenced_code", "tables", "nl2br"]
            )
        except Exception:
            import html as _html
            html_answer = "<p>" + _html.escape(filtered_answer).replace("\n", "<br>") + "</p>"

        # Sanitize HTML if bleach is available
        try:
            import bleach
            allowed_tags = [
                'p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'blockquote',
                'code', 'pre', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'table',
                'thead', 'tbody', 'tr', 'th', 'td'
            ]
            allowed_attrs = {
                'a': ['href', 'title', 'target', 'rel'],
                'code': ['class']
            }
            html_answer = bleach.clean(html_answer, tags=allowed_tags, attributes=allowed_attrs, strip=True)
        except Exception:
            pass

        # Derive plain text
        try:
            from bs4 import BeautifulSoup
            answer_text = BeautifulSoup(html_answer, "html.parser").get_text("\n")
        except Exception:
            import re as _re
            answer_text = _re.sub(r"<[^>]+>", "", html_answer)
        
        return jsonify({
            "answer": answer_text,  # processed plain text for backward compatibility
            "answer_text": answer_text,
            "answer_html": html_answer,
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