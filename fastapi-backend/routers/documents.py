"""
Document Management Router

Migrated from api/src/handlers/documents.js to provide document management
functionality within the FastAPI backend.
"""

from fastapi import APIRouter, HTTPException, Request, status, Depends, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
import logging
from typing import Optional
import asyncio

from config.database import get_db_connection, get_db_transaction, get_supabase_admin_client
from config.settings import settings
from middleware.auth import get_current_user, AuthenticatedUser
from services.parser import parser_service
from services.embedding import embedding_service
from models.schemas import (
    DocumentResponse, DocumentListResponse, DocumentUploadResponse,
    SuccessResponse, ErrorResponse
)
from utils.logging import log_service_call, log_service_result
from utils.helpers import current_timestamp, generate_uuid

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document_root(
    http_request: Request,
    file: UploadFile = File(...),
    bot_id: Optional[str] = Form(None),
    botId: Optional[str] = Form(None),  # Dashboard compatibility
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Upload a document for processing (root endpoint).
    This is the main endpoint that the dashboard uses.
    Accepts both bot_id and botId for compatibility.
    """
    # Use botId if bot_id is not provided (dashboard compatibility)
    actual_bot_id = bot_id or botId
    if not actual_bot_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="bot_id or botId is required"
        )
    
    return await upload_document(http_request, file, actual_bot_id, current_user)

@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    http_request: Request,
    file: UploadFile = File(...),
    bot_id: str = Form(...),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Upload a document for processing.
    Migrated from api/src/handlers/documents.js uploadDocument function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "DocumentsRouter",
        "upload_document",
        filename=file.filename,
        bot_id=bot_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Verify bot ownership
        async with get_db_connection() as conn:
            bot_row = await conn.fetchrow("""
                SELECT id
                FROM bots
                WHERE id = $1 AND user_id = $2
            """, bot_id, current_user.id)
            
            if not bot_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Bot not found or access denied"
                )
        
        # Check file type
        file_type = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        supported_types = ['pdf', 'txt', 'docx', 'md', 'html', 'xlsx', 'xls']
        
        if file_type not in supported_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Supported types: {', '.join(supported_types)}"
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Create file path
        file_path = f"{current_user.id}/{bot_id}/{int(current_timestamp().timestamp())}_{file.filename}"
        
        # Upload to Supabase Storage
        supabase = get_supabase_admin_client()
        
        try:
            storage_response = supabase.storage.from_("documents").upload(
                file_path,
                file_content,
                {
                    "content-type": file.content_type or "application/octet-stream",
                    "upsert": "true"  # Supabase expects string, not boolean
                }
            )
            
            if hasattr(storage_response, 'error') and storage_response.error:
                raise ValueError(f"Storage upload failed: {storage_response.error}")
                
        except Exception as storage_error:
            logger.error(f"Storage upload error: {storage_error}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload file to storage"
            )
        
        # Create document record in database
        document_id = generate_uuid()
        now = current_timestamp()
        
        async with get_db_connection() as conn:
            await conn.execute("""
                INSERT INTO documents (
                    id, bot_id, user_id, file_name, file_type, file_path, 
                    file_size, status, created_at, updated_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, 
                document_id,
                bot_id,
                current_user.id,
                file.filename,
                file_type,
                file_path,
                file_size,
                "pending",
                now,
                now
            )
        
        # Trigger parser service asynchronously
        asyncio.create_task(
            _process_document_async(document_id, file_path, file_type, bot_id)
        )
        
        log_service_result(
            logger,
            "DocumentsRouter",
            "upload_document",
            True,
            document_id=document_id,
            correlation_id=correlation_id
        )
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            file_size=file_size,
            status="pending",
            message="Document uploaded successfully and processing started"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "DocumentsRouter",
            "upload_document",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Upload document error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document upload"
        )

@router.get("", response_model=DocumentListResponse)
async def get_documents(
    bot_id: Optional[str] = Query(None, description="Bot ID to get documents for (optional)"),
    http_request: Request = None,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get all documents for a bot.
    Migrated from api/src/handlers/documents.js getDocuments function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown') if http_request else 'unknown'
    
    log_service_call(
        logger,
        "DocumentsRouter",
        "get_documents",
        bot_id=bot_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_connection() as conn:
            if bot_id:
                # Verify bot ownership if bot_id is provided
                bot_row = await conn.fetchrow("""
                    SELECT id
                    FROM bots
                    WHERE id = $1 AND user_id = $2
                """, bot_id, current_user.id)
                
                if not bot_row:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Bot not found or access denied"
                    )
                
                # Get documents for the specific bot
                document_rows = await conn.fetch("""
                    SELECT id, bot_id, file_name, file_type, file_size, status, 
                           created_at, processed_at, error
                    FROM documents
                    WHERE bot_id = $1 AND user_id = $2
                    ORDER BY created_at DESC
                """, bot_id, current_user.id)
            else:
                # Get all documents for the user
                document_rows = await conn.fetch("""
                    SELECT id, bot_id, file_name, file_type, file_size, status, 
                           created_at, processed_at, error
                    FROM documents
                    WHERE user_id = $1
                    ORDER BY created_at DESC
                """, current_user.id)
            
            documents = [
                DocumentResponse(
                    id=str(row['id']),
                    bot_id=str(row['bot_id']),
                    filename=row['file_name'],
                    file_type=row['file_type'],
                    file_size=row['file_size'],
                    status=row['status'],
                    created_at=row['created_at'],
                    processed_at=row['processed_at'],
                    error=row['error']
                )
                for row in document_rows
            ]
            
            log_service_result(
                logger,
                "DocumentsRouter",
                "get_documents",
                True,
                documents_count=len(documents),
                correlation_id=correlation_id
            )
            
            return DocumentListResponse(
                documents=documents,
                total=len(documents)
            )
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "DocumentsRouter",
            "get_documents",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Get documents error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get a specific document.
    Migrated from api/src/handlers/documents.js getDocument function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "DocumentsRouter",
        "get_document",
        document_id=document_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_connection() as conn:
            document_row = await conn.fetchrow("""
                SELECT id, bot_id, file_name, file_type, file_size, status,
                       created_at, processed_at, error
                FROM documents
                WHERE id = $1 AND user_id = $2
            """, document_id, current_user.id)
            
            if not document_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found"
                )
            
            log_service_result(
                logger,
                "DocumentsRouter",
                "get_document",
                True,
                correlation_id=correlation_id
            )
            
            return DocumentResponse(
                id=document_row['id'],
                bot_id=document_row['bot_id'],
                filename=document_row['file_name'],
                file_type=document_row['file_type'],
                file_size=document_row['file_size'],
                status=document_row['status'],
                created_at=document_row['created_at'],
                processed_at=document_row['processed_at'],
                error=document_row['error']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "DocumentsRouter",
            "get_document",
            False,
            error=str(e)
        )
        
        logger.error(f"Get document error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document"
        )

@router.get("/{document_id}/content", response_model=dict)
async def get_document_content(
    document_id: str,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Get document content for viewing.
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "DocumentsRouter",
        "get_document_content",
        document_id=document_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_connection() as conn:
            # First verify the document exists and user has access
            document_row = await conn.fetchrow("""
                SELECT id, bot_id, file_name, file_type, file_size, file_path
                FROM documents
                WHERE id = $1 AND user_id = $2
            """, document_id, current_user.id)
            
            if not document_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found or access denied"
                )
            
            # Get document chunks for content
            chunks = await conn.fetch("""
                SELECT chunk_text, chunk_index
                FROM document_chunks
                WHERE document_id = $1
                ORDER BY chunk_index
            """, document_id)
            
            # Combine chunks to form content
            content = ""
            if chunks:
                content = " ".join([chunk['chunk_text'] for chunk in chunks])
            
            # If no chunks, try to read from file path (for simple text files)
            if not content and document_row['file_type'] in ['txt', 'md']:
                try:
                    import os
                    file_path = document_row['file_path']
                    if os.path.exists(file_path):
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                except Exception as e:
                    logger.warning(f"Failed to read file content: {e}")
                    content = "Document content not available"
            
            log_service_result(
                logger,
                "DocumentsRouter",
                "get_document_content",
                True,
                correlation_id=correlation_id
            )
            
            return {
                "id": str(document_row['id']),
                "filename": document_row['file_name'],
                "file_type": document_row['file_type'],
                "file_size": document_row['file_size'],
                "content": content,
                "chunks_count": len(chunks)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "DocumentsRouter",
            "get_document_content",
            False,
            error=str(e)
        )
        
        logger.error(f"Get document content error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document content"
        )

@router.delete("/{document_id}", response_model=SuccessResponse)
async def delete_document(
    document_id: str,
    http_request: Request,
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """
    Delete a document.
    Migrated from api/src/handlers/documents.js deleteDocument function
    """
    
    correlation_id = getattr(http_request.state, 'correlation_id', 'unknown')
    
    log_service_call(
        logger,
        "DocumentsRouter",
        "delete_document",
        document_id=document_id,
        user_id=current_user.id,
        correlation_id=correlation_id
    )
    
    try:
        async with get_db_transaction() as conn:
            # Get document details
            document_row = await conn.fetchrow("""
                SELECT file_path, bot_id
                FROM documents
                WHERE id = $1 AND user_id = $2
            """, document_id, current_user.id)
            
            if not document_row:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Document not found"
                )
            
            file_path = document_row['file_path']
            bot_id = document_row['bot_id']
            
            # Delete file from storage
            try:
                supabase = get_supabase_admin_client()
                storage_response = supabase.storage.from_("documents").remove([file_path])
                
                if hasattr(storage_response, 'error') and storage_response.error:
                    logger.warning(f"Failed to delete file from storage: {storage_response.error}")
                    # Continue with database deletion even if storage deletion fails
                    
            except Exception as storage_error:
                logger.warning(f"Storage deletion error: {storage_error}")
                # Continue with database deletion
            
            # Delete document from database
            await conn.execute("""
                DELETE FROM documents
                WHERE id = $1 AND user_id = $2
            """, document_id, current_user.id)
        
        # Delete embeddings from Qdrant (async, don't wait)
        asyncio.create_task(
            _delete_document_embeddings_async(document_id, bot_id)
        )
        
        log_service_result(
            logger,
            "DocumentsRouter",
            "delete_document",
            True,
            correlation_id=correlation_id
        )
        
        return SuccessResponse(message="Document deleted successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        log_service_result(
            logger,
            "DocumentsRouter",
            "delete_document",
            False,
            error=str(e),
            correlation_id=correlation_id
        )
        
        logger.error(f"Delete document error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document"
        )

# Helper functions
async def _process_document_async(document_id: str, file_path: str, file_type: str, bot_id: str):
    """Process document asynchronously"""
    try:
        await parser_service.parse_document(document_id, file_path, file_type, bot_id)
        logger.info(f"Document {document_id} processed successfully")
    except Exception as e:
        logger.error(f"Failed to process document {document_id}: {e}", exc_info=True)

async def _delete_document_embeddings_async(document_id: str, bot_id: str):
    """Delete document embeddings asynchronously"""
    try:
        await embedding_service.delete_document_embeddings(document_id, bot_id)
        logger.info(f"Embeddings for document {document_id} deleted successfully")
    except Exception as e:
        logger.warning(f"Failed to delete embeddings for document {document_id}: {e}")