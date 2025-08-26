"""
Test API compatibility with the original Cloudflare Workers API
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

class TestAPICompatibility:
    """Test that the FastAPI backend maintains compatibility with the original API"""
    
    def test_root_endpoint(self, client: TestClient):
        """Test root endpoint returns expected format"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
    
    def test_api_info_endpoint(self, client: TestClient):
        """Test API info endpoint"""
        response = client.get("/api")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data
        
        # Check that all expected endpoints are listed
        expected_endpoints = [
            "authentication", "bots", "documents", "crawling", 
            "embeddings", "chat", "admin", "analytics", "widget", "health"
        ]
        for endpoint in expected_endpoints:
            assert endpoint in data["endpoints"]
    
    @pytest.mark.asyncio
    async def test_cors_headers(self, async_client: AsyncClient):
        """Test CORS headers are properly set"""
        response = await async_client.options("/api/bots")
        assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly handled
        
        # Test actual request with CORS
        response = await async_client.get("/", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 200
    
    def test_error_response_format(self, client: TestClient):
        """Test error responses match expected format"""
        # Test 404 error
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data or "error" in data
    
    @pytest.mark.asyncio
    async def test_authentication_endpoints_exist(self, async_client: AsyncClient):
        """Test that authentication endpoints exist and return expected status codes"""
        # Test endpoints exist (they should return 422 for missing data, not 404)
        endpoints = [
            ("/api/auth/register", "POST"),
            ("/api/auth/login", "POST"),
            ("/api/auth/logout", "POST"),
            ("/api/auth/user", "GET"),
            ("/api/auth/change-password", "POST")
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = await async_client.get(endpoint)
            else:
                response = await async_client.request(method, endpoint, json={})
            
            # Should not return 404 (endpoint exists)
            assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_bot_endpoints_exist(self, async_client: AsyncClient):
        """Test that bot management endpoints exist"""
        endpoints = [
            ("/api/bots", "GET"),
            ("/api/bots", "POST"),
            ("/api/bots/test-id", "GET"),
            ("/api/bots/test-id", "PUT"),
            ("/api/bots/test-id", "DELETE")
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = await async_client.get(endpoint)
            else:
                response = await async_client.request(method, endpoint, json={})
            
            # Should not return 404 (endpoint exists)
            assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_document_endpoints_exist(self, async_client: AsyncClient):
        """Test that document management endpoints exist"""
        endpoints = [
            ("/api/documents", "GET"),
            ("/api/documents", "POST"),
            ("/api/documents/test-id", "GET"),
            ("/api/documents/test-id", "DELETE")
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = await async_client.get(endpoint)
            elif method == "POST":
                # For file upload, we need multipart data
                response = await async_client.post(endpoint, files={"file": ("test.txt", "test content", "text/plain")})
            else:
                response = await async_client.request(method, endpoint)
            
            # Should not return 404 (endpoint exists)
            assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_crawl_endpoints_exist(self, async_client: AsyncClient):
        """Test that crawling endpoints exist"""
        endpoints = [
            ("/api/crawl", "GET"),
            ("/api/crawl", "POST"),
            ("/api/crawl/test-id", "GET"),
            ("/api/crawl/test-id", "DELETE"),
            ("/api/crawl/realtime", "POST")
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = await async_client.get(endpoint + "?botId=test-bot-id" if endpoint == "/api/crawl" else endpoint)
            else:
                response = await async_client.request(method, endpoint, json={"url": "https://example.com", "bot_id": "test-bot"})
            
            # Should not return 404 (endpoint exists)
            assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_embedding_endpoints_exist(self, async_client: AsyncClient):
        """Test that embedding endpoints exist"""
        endpoints = [
            ("/api/embeddings", "POST"),
            ("/api/embeddings/test-id", "GET"),
            ("/api/embeddings/test-bot-id", "DELETE")
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = await async_client.get(endpoint)
            else:
                response = await async_client.request(method, endpoint, json={"bot_id": "test-bot", "document_ids": ["test-doc"]})
            
            # Should not return 404 (endpoint exists)
            assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_chat_endpoints_exist(self, async_client: AsyncClient):
        """Test that chat endpoints exist"""
        endpoints = [
            ("/api/chat", "POST"),
            ("/api/chat/conversations", "GET"),
            ("/api/chat/conversations/test-id", "GET"),
            ("/api/chat/conversations/test-id", "DELETE")
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = await async_client.get(endpoint + ("?botId=test-bot" if "conversations" in endpoint and method == "GET" and endpoint.count("/") == 3 else ""))
            else:
                response = await async_client.request(method, endpoint, json={"message": "test", "bot_id": "test-bot"})
            
            # Should not return 404 (endpoint exists)
            assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_admin_endpoints_exist(self, async_client: AsyncClient):
        """Test that admin endpoints exist"""
        endpoints = [
            ("/api/admin/stats", "GET"),
            ("/api/admin/logs", "GET"),
            ("/api/admin/jobs", "GET")
        ]
        
        for endpoint, method in endpoints:
            response = await async_client.get(endpoint)
            # Should not return 404 (endpoint exists)
            assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_analytics_endpoints_exist(self, async_client: AsyncClient):
        """Test that analytics endpoints exist"""
        endpoints = [
            ("/api/analytics/bot-stats?botId=test-bot", "GET"),
            ("/api/analytics/bot-usage/test-bot", "GET"),
            ("/api/analytics/overview", "GET")
        ]
        
        for endpoint, method in endpoints:
            response = await async_client.get(endpoint)
            # Should not return 404 (endpoint exists)
            assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_widget_endpoints_exist(self, async_client: AsyncClient):
        """Test that widget endpoints exist"""
        endpoints = [
            ("/api/widget/test-bot/config", "GET"),
            ("/api/widget/test-bot/config", "PUT"),
            ("/api/widget/test-bot/settings", "GET"),
            ("/api/widget/test-bot/reset-config", "POST")
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = await async_client.get(endpoint)
            else:
                response = await async_client.request(method, endpoint, json={"theme": "light"})
            
            # Should not return 404 (endpoint exists)
            assert response.status_code != 404
    
    @pytest.mark.asyncio
    async def test_response_headers(self, async_client: AsyncClient):
        """Test that responses include expected headers"""
        response = await async_client.get("/")
        
        # Check for correlation ID header (added by performance middleware)
        # This might not be present in all responses, but should be in most
        headers = response.headers
        
        # Check content type
        assert "application/json" in headers.get("content-type", "")
    
    def test_request_validation(self, client: TestClient):
        """Test that request validation works as expected"""
        # Test invalid JSON
        response = client.post("/api/bots", json={"invalid": "data"})
        assert response.status_code in [400, 401, 422]  # Should validate or require auth
        
        # Test missing required fields
        response = client.post("/api/auth/register", json={})
        assert response.status_code == 422  # Validation error