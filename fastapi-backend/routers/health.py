"""
Health Check Router

Provides health check endpoints for monitoring the FastAPI backend
and its dependencies.
"""

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
import logging
import asyncio
from typing import Dict, Any
from datetime import datetime

from config.database import get_db_connection, get_qdrant_client, get_bedrock_client, get_supabase_admin_client
from middleware.error_handler import HealthCheckError
from utils.helpers import current_timestamp

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health", response_model=dict)
async def health_check():
    """
    Basic health check endpoint
    """
    
    return {
        "status": "healthy",
        "timestamp": current_timestamp(),
        "service": "fastapi-backend"
    }

@router.get("/health/detailed", response_model=dict)
async def detailed_health_check():
    """
    Detailed health check that tests all dependencies
    """
    
    health_status = {
        "status": "healthy",
        "timestamp": current_timestamp(),
        "service": "fastapi-backend",
        "dependencies": {}
    }
    
    overall_healthy = True
    
    # Check database connection
    try:
        async with get_db_connection() as conn:
            result = await conn.fetchval("SELECT 1")
            if result == 1:
                health_status["dependencies"]["database"] = {
                    "status": "healthy",
                    "response_time_ms": 0  # Could measure actual response time
                }
            else:
                raise Exception("Unexpected database response")
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["dependencies"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check Qdrant connection
    try:
        qdrant_client = get_qdrant_client()
        collections = qdrant_client.get_collections()
        health_status["dependencies"]["qdrant"] = {
            "status": "healthy",
            "collections_count": len(collections.collections)
        }
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        health_status["dependencies"]["qdrant"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check Bedrock connection
    try:
        bedrock_client = get_bedrock_client()
        # Simple test - list foundation models (this is a lightweight operation)
        response = bedrock_client.list_foundation_models()
        health_status["dependencies"]["bedrock"] = {
            "status": "healthy",
            "models_available": len(response.get('modelSummaries', []))
        }
    except Exception as e:
        logger.error(f"Bedrock health check failed: {e}")
        health_status["dependencies"]["bedrock"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Check Supabase connection
    try:
        supabase = get_supabase_admin_client()
        # Simple test - get auth settings (lightweight operation)
        response = supabase.auth.get_settings()
        health_status["dependencies"]["supabase"] = {
            "status": "healthy",
            "auth_enabled": bool(response)
        }
    except Exception as e:
        logger.error(f"Supabase health check failed: {e}")
        health_status["dependencies"]["supabase"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        overall_healthy = False
    
    # Set overall status
    if not overall_healthy:
        health_status["status"] = "degraded"
    
    # Return appropriate HTTP status
    status_code = status.HTTP_200_OK if overall_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=status_code,
        content=health_status
    )

@router.get("/health/database", response_model=dict)
async def database_health_check():
    """
    Specific database health check
    """
    
    try:
        start_time = datetime.utcnow()
        
        async with get_db_connection() as conn:
            # Test basic query
            result = await conn.fetchval("SELECT 1")
            
            # Test a more complex query to ensure tables exist
            count = await conn.fetchval("SELECT COUNT(*) FROM bots LIMIT 1")
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "timestamp": current_timestamp(),
                "response_time_ms": round(response_time, 2),
                "test_query_result": result,
                "tables_accessible": True
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        raise HealthCheckError("database", str(e))

@router.get("/health/qdrant", response_model=dict)
async def qdrant_health_check():
    """
    Specific Qdrant health check
    """
    
    try:
        start_time = datetime.utcnow()
        
        qdrant_client = get_qdrant_client()
        
        # Get collections info
        collections = qdrant_client.get_collections()
        
        # Get cluster info if available
        try:
            cluster_info = qdrant_client.get_cluster_info()
        except:
            cluster_info = None
        
        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds() * 1000
        
        return {
            "status": "healthy",
            "timestamp": current_timestamp(),
            "response_time_ms": round(response_time, 2),
            "collections_count": len(collections.collections),
            "collections": [c.name for c in collections.collections],
            "cluster_info": cluster_info
        }
        
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        raise HealthCheckError("qdrant", str(e))

@router.get("/health/bedrock", response_model=dict)
async def bedrock_health_check():
    """
    Specific Bedrock health check
    """
    
    try:
        start_time = datetime.utcnow()
        
        bedrock_client = get_bedrock_client()
        
        # List available foundation models
        response = bedrock_client.list_foundation_models()
        models = response.get('modelSummaries', [])
        
        # Check if our embedding model is available
        embedding_model_available = any(
            model.get('modelId') == 'amazon.titan-embed-text-v2:0' 
            for model in models
        )
        
        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds() * 1000
        
        return {
            "status": "healthy",
            "timestamp": current_timestamp(),
            "response_time_ms": round(response_time, 2),
            "models_available": len(models),
            "embedding_model_available": embedding_model_available,
            "region": bedrock_client._client_config.region_name
        }
        
    except Exception as e:
        logger.error(f"Bedrock health check failed: {e}")
        raise HealthCheckError("bedrock", str(e))

@router.get("/health/supabase", response_model=dict)
async def supabase_health_check():
    """
    Specific Supabase health check
    """
    
    try:
        start_time = datetime.utcnow()
        
        supabase = get_supabase_admin_client()
        
        # Test auth service
        auth_settings = supabase.auth.get_settings()
        
        # Test storage service by listing buckets
        try:
            buckets = supabase.storage.list_buckets()
            storage_healthy = True
            buckets_count = len(buckets)
        except Exception as storage_error:
            logger.warning(f"Supabase storage check failed: {storage_error}")
            storage_healthy = False
            buckets_count = 0
        
        end_time = datetime.utcnow()
        response_time = (end_time - start_time).total_seconds() * 1000
        
        return {
            "status": "healthy",
            "timestamp": current_timestamp(),
            "response_time_ms": round(response_time, 2),
            "auth_service": "healthy" if auth_settings else "unknown",
            "storage_service": "healthy" if storage_healthy else "degraded",
            "storage_buckets_count": buckets_count
        }
        
    except Exception as e:
        logger.error(f"Supabase health check failed: {e}")
        raise HealthCheckError("supabase", str(e))

@router.get("/health/services", response_model=dict)
async def services_health_check():
    """
    Check health of all internal services
    """
    
    services_status = {
        "timestamp": current_timestamp(),
        "services": {}
    }
    
    # Test each service by importing and checking basic functionality
    try:
        from services.crawler import crawler_service
        services_status["services"]["crawler"] = {"status": "available"}
    except Exception as e:
        services_status["services"]["crawler"] = {"status": "error", "error": str(e)}
    
    try:
        from services.parser import parser_service
        services_status["services"]["parser"] = {"status": "available"}
    except Exception as e:
        services_status["services"]["parser"] = {"status": "error", "error": str(e)}
    
    try:
        from services.embedding import embedding_service
        services_status["services"]["embedding"] = {"status": "available"}
    except Exception as e:
        services_status["services"]["embedding"] = {"status": "error", "error": str(e)}
    
    try:
        from services.rag import rag_service
        services_status["services"]["rag"] = {"status": "available"}
    except Exception as e:
        services_status["services"]["rag"] = {"status": "error", "error": str(e)}
    
    try:
        from services.realtime_crawler import realtime_crawl_service
        services_status["services"]["realtime_crawler"] = {"status": "available"}
    except Exception as e:
        services_status["services"]["realtime_crawler"] = {"status": "error", "error": str(e)}
    
    # Check if any services have errors
    all_healthy = all(
        service.get("status") == "available" 
        for service in services_status["services"].values()
    )
    
    services_status["overall_status"] = "healthy" if all_healthy else "degraded"
    
    status_code = status.HTTP_200_OK if all_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    
    return JSONResponse(
        status_code=status_code,
        content=services_status
    )

@router.get("/ready", response_model=dict)
async def readiness_check():
    """
    Kubernetes-style readiness check
    """
    
    try:
        # Quick check of critical dependencies
        async with get_db_connection() as conn:
            await conn.fetchval("SELECT 1")
        
        return {
            "status": "ready",
            "timestamp": current_timestamp()
        }
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "timestamp": current_timestamp(),
                "error": str(e)
            }
        )

@router.get("/live", response_model=dict)
async def liveness_check():
    """
    Kubernetes-style liveness check
    """
    
    return {
        "status": "alive",
        "timestamp": current_timestamp()
    }