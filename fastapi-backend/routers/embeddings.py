"""
Embeddings Router

Migrated from api/src/handlers/embeddings.js to provide embedding generation
and management functionality within the FastAPI backend.
"""

from fastapi import APIRouter, HTTPException, Request, status, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
from typing import List

from config.database import get_db_connection, get_db_transaction
from middleware.auth import get_current_user, AuthenticatedUser
from services.embedding import embedding_service
from models.schemas import (
    GenerateEmbeddingsRequest, EmbeddingJobResponse,
    SuccessResponse, ErrorResponse
)
from utils.logging import log_service_call, log_service_result
from utils.helpers import current_timestamp, generate_uuid

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("", response_model=EmbeddingJobResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_embeddings(
    request: GenerateEmbeddingsRequest,
    http_request: Request,
    background_tasks: BackgroundTasks,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Generate embeddings for documents.
    Migrated from api/src/handlers/embeddings.js generateEmbeddings function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "EmbeddingsRouter",
        "generate_embeddings",
        bot_id=request.bot_id,
        document_count=len(request.document_ids),
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_connection() as conn:
            # Verify bot ownership
            bot_row = await conn.fetchrow("""
                SELECT id FROM bots
                WHERE id = $1 AND user_id = $2
            """, request.bot_id, current_user.id)
            
            if not bot_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot not found or access denied"
                )
            
            # Verify document ownership and status
            doc_rows = await conn.fetch("""
                SELECT id, file_path, file_type, status
                FROM documents
                WHERE id = ANY($1) AND bot_id = $2 AND user_id = $3
            """, request.document_ids, request.bot_id, current_user.id)
            
            if not doc_rows:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No valid documents found"
                )
            
            found_doc_ids = [row['id'] for row in doc_rows]
            if len(found_doc_ids) != len(request.document_ids):
                missing_ids = set(request.document_ids) - set(found_doc_ids)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Documents not found: {list(missing_ids)}"
                )
            
            # Check if all documents are processed
            unprocessed_docs = [row for row in doc_rows if row['status'] != 'processed']
            if unprocessed_docs:
                unprocessed_ids = [doc['id'] for doc in unprocessed_docs]
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Some documents are not ready for embedding: {unprocessed_ids}"
                )
        
        # Create embedding job
        job_id = generate_uuid()
        now = current_timestamp()
        
        async with get_db_transaction() as conn:
            await conn.execute("""
                INSERT INTO embedding_jobs (
                    id, bot_id, user_id, document_ids, total_documents,
                    status, created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, 
                job_id,
                request.bot_id,
                current_user.id,
                request.document_ids,
                len(request.document_ids),
                'pending',
                now,
                now
            )
            
            # Update documents to embedding status
            await conn.execute("""
                UPDATE documents 
                SET status = 'embedding', updated_at = $1
                WHERE id = ANY($2) AND user_id = $3
            """, now, request.document_ids, current_user.id)
        
        # Start embedding process in background
        background_tasks.add_task(
            _run_embedding_job,
            job_id,
            request.bot_id,
            request.document_ids,
            current_user.id
        )
        
        log_service_result(
            logger,
            "EmbeddingsRouter",
            "generate_embeddings",
            True,
            job_id=job_id,
            correlation_id=correlation_id
        )
        
        return EmbeddingJobResponse(
            job_id=job_id,
            message="Embedding job started successfully",
            status="pending"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "EmbeddingsRouter",
            "generate_embeddings",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Generate embeddings error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start embedding job"
        )

@router.get("/{job_id}", response_model=dict)
async def get_embedding_status(
    job_id: str,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get the status of an embedding job.
    Migrated from api/src/handlers/embeddings.js getEmbeddingStatus function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "EmbeddingsRouter",
        "get_embedding_status",
        job_id=job_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        # Get status from embedding service
        job_data = await embedding_service.get_embedding_job_status(job_id)
        
        if not job_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Embedding job not found"
            )
        
        # Verify ownership
        async with get_db_connection() as conn:
            job_row = await conn.fetchrow("""
                SELECT id FROM embedding_jobs
                WHERE id = $1 AND user_id = $2
            """, job_id, current_user.id)
            
            if not job_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Embedding job not found"
                )
        
        log_service_result(
            logger,
            "EmbeddingsRouter",
            "get_embedding_status",
            True,
            correlation_id=correlation_id
        )
        
        return {"job": job_data}
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "EmbeddingsRouter",
            "get_embedding_status",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Get embedding status error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get embedding status"
        )

@router.delete("/{bot_id}", response_model=SuccessResponse)
async def delete_embeddings(
    bot_id: str,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Delete all embeddings for a bot.
    Migrated from api/src/handlers/embeddings.js deleteEmbeddings function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "EmbeddingsRouter",
        "delete_embeddings",
        bot_id=bot_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_transaction() as conn:
            # Verify bot ownership
            bot_row = await conn.fetchrow("""
                SELECT id FROM bots
                WHERE id = $1 AND user_id = $2
            """, bot_id, current_user.id)
            
            if not bot_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot not found or access denied"
                )
            
            # Reset document status from embedded back to processed
            await conn.execute("""
                UPDATE documents 
                SET status = 'processed', updated_at = $1
                WHERE bot_id = $2 AND user_id = $3 AND status = 'embedded'
            """, current_timestamp(), bot_id, current_user.id)
        
        # Delete embeddings from Qdrant and database
        try:
            result = await embedding_service.delete_collection_embeddings(bot_id)
            message = result.get('message', 'Embeddings deleted successfully')
        except Exception as e:
            logger.error(f"Failed to delete embeddings from Qdrant: {e}")
            # Continue anyway - at least we reset the document status
            message = "Embeddings deletion completed (some errors occurred)"
        
        log_service_result(
            logger,
            "EmbeddingsRouter",
            "delete_embeddings",
            True,
            correlation_id=correlation_id
        )
        
        return SuccessResponse(message=message)
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "EmbeddingsRouter",
            "delete_embeddings",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Delete embeddings error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete embeddings"
        )

@router.delete("/documents/{document_id}", response_model=SuccessResponse)
async def delete_document_embeddings(
    document_id: str,
    bot_id: str,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Delete embeddings for a specific document.
    Additional endpoint not in original API but useful for document management
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "EmbeddingsRouter",
        "delete_document_embeddings",
        document_id=document_id,
        bot_id=bot_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_transaction() as conn:
            # Verify document ownership
            doc_row = await conn.fetchrow("""
                SELECT id FROM documents
                WHERE id = $1 AND bot_id = $2 AND user_id = $3
            """, document_id, bot_id, current_user.id)
            
            if not doc_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found or access denied"
                )
            
            # Reset document status from embedded back to processed
            await conn.execute("""
                UPDATE documents 
                SET status = 'processed', updated_at = $1
                WHERE id = $2 AND user_id = $3
            """, current_timestamp(), document_id, current_user.id)
        
        # Delete document embeddings from Qdrant and database
        try:
            result = await embedding_service.delete_document_embeddings(document_id, bot_id)
            message = result.get('message', 'Document embeddings deleted successfully')
        except Exception as e:
            logger.error(f"Failed to delete document embeddings: {e}")
            message = "Document embeddings deletion completed (some errors occurred)"
        
        log_service_result(
            logger,
            "EmbeddingsRouter",
            "delete_document_embeddings",
            True,
            correlation_id=correlation_id
        )
        
        return SuccessResponse(message=message)
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "EmbeddingsRouter",
            "delete_document_embeddings",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Delete document embeddings error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document embeddings"
        )

@router.post("/create-collection/{bot_id}", response_model=dict)
async def create_collection(
    bot_id: str,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Create a Qdrant collection for a bot.
    Additional endpoint for explicit collection management
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "EmbeddingsRouter",
        "create_collection",
        bot_id=bot_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        # Verify bot ownership
        async with get_db_connection() as conn:
            bot_row = await conn.fetchrow("""
                SELECT id FROM bots
                WHERE id = $1 AND user_id = $2
            """, bot_id, current_user.id)
            
            if not bot_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot not found or access denied"
                )
        
        # Create collection
        result = await embedding_service.create_collection(bot_id)
        
        log_service_result(
            logger,
            "EmbeddingsRouter",
            "create_collection",
            True,
            correlation_id=correlation_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "EmbeddingsRouter",
            "create_collection",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Create collection error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create collection"
        )

@router.get("/collection/{bot_id}/info", response_model=dict)
async def get_collection_info(
    bot_id: str,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get information about a Qdrant collection.
    Additional endpoint for collection monitoring
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "EmbeddingsRouter",
        "get_collection_info",
        bot_id=bot_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        # Verify bot ownership
        async with get_db_connection() as conn:
            bot_row = await conn.fetchrow("""
                SELECT id FROM bots
                WHERE id = $1 AND user_id = $2
            """, bot_id, current_user.id)
            
            if not bot_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot not found or access denied"
                )
        
        # Get collection info
        result = await embedding_service.get_collection_info(bot_id)
        
        log_service_result(
            logger,
            "EmbeddingsRouter",
            "get_collection_info",
            True,
            correlation_id=correlation_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "EmbeddingsRouter",
            "get_collection_info",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Get collection info error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get collection info"
        )

# Background task functions

async def _run_embedding_job(
    job_id: str,
    bot_id: str,
    document_ids: List[str],
    user_id: str
):
    """Run embedding job in background"""
    
    try:
        await embedding_service.embed_documents(
            job_id=job_id,
            bot_id=bot_id,
            document_ids=document_ids
        )
        
        # Update document status to embedded
        async with get_db_connection() as conn:
            await conn.execute("""
                UPDATE documents 
                SET status = 'embedded', updated_at = $1
                WHERE id = ANY($2) AND user_id = $3
            """, current_timestamp(), document_ids, user_id)
            
    except Exception as e:
        logger.error(f"Background embedding job {job_id} failed: {e}", exc_info=True)
        
        # Revert document status back to processed
        try:
            async with get_db_connection() as conn:
                await conn.execute("""
                    UPDATE documents 
                    SET status = 'processed', updated_at = $1
                    WHERE id = ANY($2) AND user_id = $3
                """, current_timestamp(), document_ids, user_id)
        except Exception as revert_error:
            logger.error(f"Failed to revert document status: {revert_error}")