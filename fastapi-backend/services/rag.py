"""
RAG Service

Migrated from rag_service.py to provide question-answering functionality
using retrieval-augmented generation within the FastAPI backend.
"""

import asyncio
import logging
import json
import time
from typing import List, Dict, Any, Optional
import httpx

from config.database import get_qdrant_client, get_bedrock_client
from config.settings import settings
from utils.logging import log_service_call, log_service_result, log_external_service_call
from utils.helpers import filter_ai_response

logger = logging.getLogger(__name__)

class RAGService:
    """Service for RAG (Retrieval-Augmented Generation) operations"""
    
    def __init__(self):
        self.logger = logger
        self.embedding_model_id = settings.BEDROCK_EMBEDDING_MODEL
        self.llm_model_id = settings.BEDROCK_RAG_MODEL
    
    async def process_chat(
        self,
        query: str,
        bot_id: str,
        conversation_id: Optional[str] = None,
        message_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process a chat query using RAG pipeline.
        Migrated from rag_service.py /chat endpoint
        """
        
        log_service_call(
            self.logger,
            "RAGService",
            "process_chat",
            query=query[:50] + "..." if len(query) > 50 else query,
            bot_id=bot_id,
            conversation_id=conversation_id,
            message_history_length=len(message_history) if message_history else 0
        )
        
        if message_history is None:
            message_history = []
        
        try:
            # 1. Embed user question
            self.logger.info("Embedding user query...")
            start_time = time.time()
            query_embedding = await self._generate_query_embedding(query)
            self.logger.info(f"Query embedded in {time.time() - start_time:.2f} seconds")
            
            # 2. Search for relevant documents in Qdrant
            search_results = await self._search_relevant_documents(query_embedding, bot_id)
            
            if not search_results:
                self.logger.warning("No relevant documents found in vector database")
            
            # 3. Assemble context from search results
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
            self.logger.info(f"Context assembled: {len(context)} characters")
            
            # 4. Include chat history if available
            chat_history = self._format_chat_history(message_history)
            self.logger.info(f"Chat history formatted: {len(chat_history)} characters")
            
            # 5. Build prompt with context and history
            prompt = self._build_prompt(context, chat_history, query)
            self.logger.info(f"Prompt built: {len(prompt)} characters")
            
            # 6. Generate answer using LLM
            answer = await self._generate_answer(prompt)
            
            # 7. Filter and format the response
            filtered_answer = filter_ai_response(answer)
            
            # Build HTML and plain-text variants for frontend consumption
            answer_html = await self._format_answer_html(filtered_answer)
            answer_text = await self._format_answer_text(answer_html)
            
            # Calculate tokens used (approximate)
            tokens_used = len(prompt.split()) + len(answer.split())
            
            result = {
                "answer": answer_text,  # processed plain text for backward compatibility
                "answer_text": answer_text,
                "answer_html": answer_html,
                "sources": sources,
                "tokens_used": tokens_used,
                "conversation_id": conversation_id or "new"
            }
            
            log_service_result(
                self.logger,
                "RAGService",
                "process_chat",
                True,
                tokens_used=tokens_used,
                sources_count=len(sources)
            )
            
            return result
            
        except Exception as e:
            log_service_result(
                self.logger,
                "RAGService",
                "process_chat",
                False,
                error=str(e)
            )
            
            # Return error response in expected format
            return {
                "answer": "I'm sorry, I'm having trouble processing your request right now. Please try again later.",
                "answer_text": "I'm sorry, I'm having trouble processing your request right now. Please try again later.",
                "answer_html": "<p>I'm sorry, I'm having trouble processing your request right now. Please try again later.</p>",
                "sources": [],
                "tokens_used": 0,
                "conversation_id": conversation_id or "new",
                "error": f"Failed to process chat request: {str(e)}"
            }
    
    async def _generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for the user query using Bedrock"""
        
        try:
            bedrock_client = get_bedrock_client()
            
            log_external_service_call(
                self.logger,
                "AWS Bedrock",
                f"invoke_model/{self.embedding_model_id}",
                query_length=len(query)
            )
            
            response = bedrock_client.invoke_model(
                body=json.dumps({"inputText": query}),
                modelId=self.embedding_model_id,
                accept="application/json",
                contentType="application/json"
            )
            
            response_body = json.loads(response.get("body").read())
            embedding = response_body.get("embedding")
            
            if not embedding:
                raise ValueError(f"No embedding in response: {response_body}")
            
            return embedding
            
        except Exception as e:
            self.logger.error(f"Failed to generate query embedding: {e}", exc_info=True)
            raise
    
    async def _search_relevant_documents(
        self,
        query_embedding: List[float],
        bot_id: str,
        limit: int = 5
    ) -> List[Any]:
        """Search for relevant documents in Qdrant"""
        
        try:
            qdrant_client = get_qdrant_client()
            
            log_external_service_call(
                self.logger,
                "Qdrant",
                f"search/{bot_id}",
                embedding_length=len(query_embedding),
                limit=limit
            )
            
            # Check if collection exists
            collections = qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if bot_id not in collection_names:
                self.logger.error(f"Collection '{bot_id}' does not exist!")
                self.logger.error(f"Available collections: {collection_names}")
                return []
            
            # Get collection info
            collection_info = qdrant_client.get_collection(bot_id)
            self.logger.info(f"Collection '{bot_id}' has {collection_info.points_count} points")
            
            if collection_info.points_count == 0:
                self.logger.warning(f"Collection '{bot_id}' exists but has no documents!")
                return []
            
            # Perform the search
            start_time = time.time()
            search_results = qdrant_client.search(
                collection_name=bot_id,
                query_vector=query_embedding,
                limit=limit
            )
            
            self.logger.info(f"Qdrant search completed in {time.time() - start_time:.2f} seconds")
            self.logger.info(f"Found {len(search_results)} relevant chunks")
            
            if search_results:
                self.logger.info(f"First result score: {search_results[0].score}")
                self.logger.debug(f"First result preview: {search_results[0].payload.get('chunk', '')[:100]}...")
            else:
                self.logger.warning("Search returned no results - check embedding similarity")
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Error in Qdrant search: {e}", exc_info=True)
            return []
    
    def _format_chat_history(self, message_history: List[Dict[str, str]]) -> str:
        """Format message history for the prompt"""
        
        if not message_history:
            return ""
        
        formatted = "\n\nChat History:\n"
        for msg in message_history:
            role = "User" if msg["role"] == "user" else "Assistant"
            formatted += f"{role}: {msg['content']}\n"
        
        return formatted
    
    def _build_prompt(self, context: str, chat_history: str, query: str) -> str:
        """Build the prompt for the LLM"""
        
        prompt = f"""Answer the user's question based on the following context. If you cannot find the answer in the context, say that you don't know but provide your best guess based on general knowledge.

Context:
{context}
{chat_history}

User Question: {query}

Answer:"""
        
        return prompt
    
    async def _generate_answer(self, prompt: str) -> str:
        """Generate answer using Bedrock GPT model"""
        
        try:
            bedrock_client = get_bedrock_client()
            
            log_external_service_call(
                self.logger,
                "AWS Bedrock",
                f"invoke_model/{self.llm_model_id}",
                prompt_length=len(prompt)
            )
            
            start_time = time.time()
            
            # Format request for OpenAI GPT model on Bedrock
            body = json.dumps({
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_completion_tokens": 2000,
                "temperature": 0.7,
                "top_p": 0.9
            })
            
            response = bedrock_client.invoke_model(
                body=body,
                modelId=self.llm_model_id,
                accept="application/json",
                contentType="application/json"
            )
            
            response_body = json.loads(response.get("body").read())
            
            # Extract the generated text from the OpenAI response format
            answer = ""
            if "choices" in response_body and len(response_body["choices"]) > 0:
                choice = response_body["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    answer = choice["message"]["content"].strip()
            
            # Fallback to other formats if needed
            if not answer:
                answer = (
                    response_body.get("completion", "") or 
                    response_body.get("text", "") or
                    response_body.get("generated_text", "")
                ).strip()
            
            if not answer:
                self.logger.error(f"No answer in Bedrock response: {response_body}")
                raise Exception("Empty response from Bedrock")
            
            self.logger.info(f"Bedrock response received in {time.time() - start_time:.2f} seconds")
            self.logger.info(f"Generated answer ({len(answer)} chars): {answer[:100]}...")
            
            return answer
                
        except Exception as e:
            self.logger.error(f"Bedrock generation failed: {e}", exc_info=True)
            return "I'm sorry, I'm having trouble connecting to my language model right now. Please check the configuration and try again."
    

    
    async def _format_answer_html(self, answer: str) -> str:
        """Format answer as HTML"""
        
        try:
            import markdown
            html_answer = markdown.markdown(
                answer,
                extensions=["fenced_code", "tables", "nl2br"]
            )
            
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
            except ImportError:
                pass
            
            return html_answer
            
        except ImportError:
            # Fallback to simple HTML escaping
            import html
            return "<p>" + html.escape(answer).replace("\n", "<br>") + "</p>"
    
    async def _format_answer_text(self, html_answer: str) -> str:
        """Extract plain text from HTML answer"""
        
        try:
            from bs4 import BeautifulSoup
            return BeautifulSoup(html_answer, "html.parser").get_text("\n")
        except ImportError:
            # Fallback to regex-based HTML stripping
            import re
            return re.sub(r"<[^>]+>", "", html_answer)

# Global service instance
rag_service = RAGService()