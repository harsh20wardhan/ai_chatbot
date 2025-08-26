"""
Embedding Service

Migrated from embedding_service.py to provide text embedding functionality
within the FastAPI backend.
"""

import asyncio
import logging
import json
from typing import List, Dict, Any, Optional
import uuid

from config.database import get_db_connection, get_db_transaction, get_qdrant_client, get_bedrock_client
from config.settings import settings
from utils.logging import log_service_call, log_service_result, log_external_service_call
from utils.helpers import current_timestamp, generate_uuid, chunk_text

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for text embedding operations"""
    
    def __init__(self):
        self.logger = logger
        self.embedding_model_id = "amazon.titan-embed-text-v2:0"
    
    async def generate_embeddings_job(
        self,
        job_id: str,
        bot_id: str,
        document_ids: List[str]
    ) -> Dict[str, Any]:
        """
        Process embedding job for multiple documents.
        Migrated from embedding_service.py /embed endpoint
        """
        
        log_service_call(
            self.logger,
            "EmbeddingService",
            "generate_embeddings_job",
            job_id=job_id,
            bot_id=bot_id,
            document_count=len(document_ids)
        )
        
        try:
            # Update job status to running
            await self._update_embedding_job_status(job_id, "running")
            
            processed_count = 0
            
            for doc_id in document_ids:
                try:
                    # Get document content from database
                    document_content = await self._get_document_content(doc_id)
                    
                    if not document_content:
                        self.logger.warning(f"No content found for document {doc_id}")
                        continue
                    
                    # Split text into chunks
                    chunks = chunk_text(document_content)
                    self.logger.info(f"Document {doc_id}: split into {len(chunks)} chunks")
                    
                    # Generate embeddings using Bedrock
                    embeddings = await self._generate_embeddings(chunks)
                    self.logger.info(f"Generated {len(embeddings)} embeddings with {len(embeddings[0])} dimensions")
                    
                    # Ensure collection exists
                    await self._ensure_qdrant_collection(bot_id, len(embeddings[0]) if embeddings else 1024)
                    
                    # Prepare points for Qdrant
                    points = []
                    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                        point_id = generate_uuid()
                        points.append({
                            "id": point_id,
                            "vector": embedding,
                            "payload": {
                                "document_id": doc_id,
                                "chunk_index": i,
                                "chunk": chunk,
                                "source_type": "document"
                            }
                        })
                    
                    # Upsert points to Qdrant
                    qdrant_client = get_qdrant_client()
                    qdrant_client.upsert(
                        collection_name=bot_id,
                        points=points
                    )
                    self.logger.info(f"Upserted {len(points)} points to collection {bot_id}")
                    
                    processed_count += 1
                    
                except Exception as e:
                    self.logger.error(f"Error processing document {doc_id}: {e}", exc_info=True)
                    continue
            
            # Update job status to completed
            await self._update_embedding_job_status(job_id, "completed", processed_count)
            
            log_service_result(
                self.logger,
                "EmbeddingService",
                "generate_embeddings_job",
                True,
                documents_processed=processed_count
            )
            
            return {
                "status": "completed",
                "job_id": job_id,
                "documents_processed": processed_count
            }
            
        except Exception as e:
            # Update job status to failed
            await self._update_embedding_job_status(job_id, "failed", error=str(e))
            
            log_service_result(
                self.logger,
                "EmbeddingService",
                "generate_embeddings_job",
                False,
                error=str(e)
            )
            
            raise
    
    async def delete_document_embeddings(
        self,
        document_id: str,
        bot_id: str
    ) -> Dict[str, Any]:
        """
        Delete embeddings for a specific document.
        Migrated from embedding_service.py /documents/<document_id>/delete endpoint
        """
        
        log_service_call(
            self.logger,
            "EmbeddingService",
            "delete_document_embeddings",
            document_id=document_id,
            bot_id=bot_id
        )
        
        try:
            qdrant_client = get_qdrant_client()
            
            # Delete embeddings for document from Qdrant using filter
            qdrant_client.delete(
                collection_name=bot_id,
                points_selector={
                    "filter": {
                        "must": [
                            {"key": "document_id", "match": {"value": document_id}}
                        ]
                    }
                }
            )
            
            self.logger.info(f"Deleted embeddings for document {document_id} from collection {bot_id}")
            
            log_service_result(
                self.logger,
                "EmbeddingService",
                "delete_document_embeddings",
                True
            )
            
            return {"status": "success"}
            
        except Exception as e:
            log_service_result(
                self.logger,
                "EmbeddingService",
                "delete_document_embeddings",
                False,
                error=str(e)
            )
            
            self.logger.error(f"Error deleting embeddings: {e}", exc_info=True)
            raise
    
    async def delete_all_embeddings(self, bot_id: str) -> Dict[str, Any]:
        """
        Delete all embeddings for a bot (entire collection).
        Migrated from embedding_service.py /delete_all endpoint
        """
        
        log_service_call(
            self.logger,
            "EmbeddingService",
            "delete_all_embeddings",
            bot_id=bot_id
        )
        
        try:
            qdrant_client = get_qdrant_client()
            
            # Delete the entire collection
            qdrant_client.delete_collection(collection_name=bot_id)
            self.logger.info(f"Deleted collection {bot_id}")
            
            log_service_result(
                self.logger,
                "EmbeddingService",
                "delete_all_embeddings",
                True
            )
            
            return {"status": "success"}
            
        except Exception as e:
            log_service_result(
                self.logger,
                "EmbeddingService",
                "delete_all_embeddings",
                False,
                error=str(e)
            )
            
            self.logger.error(f"Error deleting collection: {e}", exc_info=True)
            raise
    
    async def get_embedding_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get embedding job status"""
        
        try:
            async with get_db_connection() as conn:
                row = await conn.fetchrow("""
                    SELECT id, bot_id, status, documents_processed, total_documents,
                           created_at, updated_at, completed_at, error
                    FROM embedding_jobs 
                    WHERE id = $1
                """, job_id)
                
                if not row:
                    return None
                
                return {
                    "job_id": row['id'],
                    "bot_id": row['bot_id'],
                    "status": row['status'],
                    "documents_processed": row['documents_processed'] or 0,
                    "total_documents": row['total_documents'] or 0,
                    "created_at": row['created_at'],
                    "updated_at": row['updated_at'],
                    "completed_at": row['completed_at'],
                    "error": row['error']
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get embedding job status: {e}", exc_info=True)
            raise
    
    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Amazon Titan"""
        
        embeddings = []
        bedrock_client = get_bedrock_client()
        
        for text in texts:
            try:
                log_external_service_call(
                    self.logger,
                    "AWS Bedrock",
                    f"invoke_model/{self.embedding_model_id}",
                    text_length=len(text)
                )
                
                response = bedrock_client.invoke_model(
                    modelId=self.embedding_model_id,
                    body=json.dumps({"inputText": text})
                )
                
                response_body = json.loads(response['body'].read())
                embedding = response_body['embedding']
                embeddings.append(embedding)
                
            except Exception as e:
                self.logger.error(f"Error generating embedding: {e}", exc_info=True)
                raise
        
        return embeddings
    
    async def _ensure_qdrant_collection(self, bot_id: str, vector_size: int = 1024):
        """Ensure Qdrant collection exists with correct dimensions"""
        
        try:
            qdrant_client = get_qdrant_client()
            
            collections = qdrant_client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if bot_id not in collection_names:
                qdrant_client.create_collection(
                    collection_name=bot_id,
                    vectors_config={"size": vector_size, "distance": "Cosine"}
                )
                self.logger.info(f"Created collection {bot_id} with {vector_size} dimensions")
            else:
                self.logger.info(f"Collection {bot_id} already exists")
                
        except Exception as e:
            self.logger.error(f"Error checking/creating collection: {e}", exc_info=True)
            raise
    
    async def _get_document_content(self, document_id: str) -> Optional[str]:
        """Get document content from database or generate dummy content"""
        
        try:
            # In a real implementation, fetch the actual document content from database
            # For now, using dummy data as in the original implementation
            dummy_content = f"This is sample content for document {document_id}. It would normally be fetched from the database."
            
            self.logger.debug(f"Retrieved content for document {document_id}: {len(dummy_content)} characters")
            return dummy_content
            
        except Exception as e:
            self.logger.error(f"Error getting document content: {e}", exc_info=True)
            return None
    
    async def _update_embedding_job_status(
        self,
        job_id: str,
        status: str,
        documents_processed: Optional[int] = None,
        error: Optional[str] = None
    ):
        """Update embedding job status in database"""
        
        try:
            async with get_db_connection() as conn:
                query = """
                    UPDATE embedding_jobs 
                    SET status = $1, updated_at = $2
                """
                params = [status, current_timestamp()]
                
                if documents_processed is not None:
                    query += ", documents_processed = $3"
                    params.append(documents_processed)
                
                if status == "completed":
                    query += f", completed_at = ${len(params) + 1}"
                    params.append(current_timestamp())
                
                if error:
                    query += f", error = ${len(params) + 1}"
                    params.append(error)
                
                query += f" WHERE id = ${len(params) + 1}"
                params.append(job_id)
                
                await conn.execute(query, *params)
                
                self.logger.debug(f"Updated embedding job {job_id} status to {status}")
                
        except Exception as e:
            self.logger.error(f"Failed to update embedding job status: {e}", exc_info=True)
            # Don't raise here as this is a secondary operation
    
    async def create_embedding_job(
        self,
        bot_id: str,
        document_ids: List[str],
        user_id: str
    ) -> str:
        """Create a new embedding job"""
        
        try:
            job_id = generate_uuid()
            
            async with get_db_connection() as conn:
                await conn.execute("""
                    INSERT INTO embedding_jobs (
                        id, bot_id, user_id, status, total_documents, 
                        documents_processed, created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, 
                    job_id,
                    bot_id,
                    user_id,
                    "pending",
                    len(document_ids),
                    0,
                    current_timestamp(),
                    current_timestamp()
                )
            
            self.logger.info(f"Created embedding job {job_id} for {len(document_ids)} documents")
            return job_id
            
        except Exception as e:
            self.logger.error(f"Failed to create embedding job: {e}", exc_info=True)
            raise

# Global service instance
embedding_service = EmbeddingService()