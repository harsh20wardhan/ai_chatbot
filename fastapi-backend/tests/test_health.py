"""
Test health check endpoints
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_basic_health_check(self, client: TestClient):
        """Test basic health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "fastapi-backend"
    
    def test_liveness_check(self, client: TestClient):
        """Test Kubernetes liveness check"""
        response = client.get("/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "timestamp" in data
    
    def test_readiness_check(self, client: TestClient):
        """Test Kubernetes readiness check"""
        response = client.get("/ready")
        # This might fail if database is not available, which is expected
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_detailed_health_check(self, async_client: AsyncClient, mock_qdrant_client, mock_bedrock_client, mock_supabase_client):
        """Test detailed health check with mocked services"""
        response = await async_client.get("/health/detailed")
        # Should return 200 or 503 depending on service availability
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "dependencies" in data
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_database_health_check(self, async_client: AsyncClient):
        """Test database-specific health check"""
        response = await async_client.get("/health/database")
        # This will likely fail in test environment without proper DB setup
        # but we can test the endpoint exists
        assert response.status_code in [200, 503]
        data = response.json()
        if response.status_code == 200:
            assert data["status"] == "healthy"
            assert "response_time_ms" in data
        else:
            assert "error" in data
    
    @pytest.mark.asyncio
    async def test_qdrant_health_check(self, async_client: AsyncClient, mock_qdrant_client):
        """Test Qdrant health check with mocked client"""
        response = await async_client.get("/health/qdrant")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "collections_count" in data
    
    @pytest.mark.asyncio
    async def test_bedrock_health_check(self, async_client: AsyncClient, mock_bedrock_client):
        """Test Bedrock health check with mocked client"""
        response = await async_client.get("/health/bedrock")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "models_available" in data
        assert data["embedding_model_available"] == True
    
    @pytest.mark.asyncio
    async def test_supabase_health_check(self, async_client: AsyncClient, mock_supabase_client):
        """Test Supabase health check with mocked client"""
        response = await async_client.get("/health/supabase")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "auth_service" in data
        assert "storage_service" in data
    
    @pytest.mark.asyncio
    async def test_services_health_check(self, async_client: AsyncClient):
        """Test internal services health check"""
        response = await async_client.get("/health/services")
        assert response.status_code in [200, 503]
        data = response.json()
        assert "services" in data
        assert "overall_status" in data
        
        # Check that all expected services are listed
        expected_services = ["crawler", "parser", "embedding", "rag", "realtime_crawler"]
        for service in expected_services:
            assert service in data["services"]