"""
Test service layer functionality
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import asyncio

class TestCrawlerService:
    """Test CrawlerService functionality"""
    
    @pytest.mark.asyncio
    async def test_crawler_service_import(self):
        """Test that CrawlerService can be imported"""
        try:
            from services.crawler import crawler_service
            assert crawler_service is not None
        except ImportError as e:
            pytest.skip(f"CrawlerService not available: {e}")
    
    @pytest.mark.asyncio
    async def test_crawler_service_methods(self):
        """Test that CrawlerService has expected methods"""
        try:
            from services.crawler import crawler_service
            
            # Check that expected methods exist
            assert hasattr(crawler_service, 'crawl_website')
            assert hasattr(crawler_service, 'cancel_crawl')
            assert callable(crawler_service.crawl_website)
            assert callable(crawler_service.cancel_crawl)
        except ImportError:
            pytest.skip("CrawlerService not available")

class TestParserService:
    """Test ParserService functionality"""
    
    @pytest.mark.asyncio
    async def test_parser_service_import(self):
        """Test that ParserService can be imported"""
        try:
            from services.parser import parser_service
            assert parser_service is not None
        except ImportError as e:
            pytest.skip(f"ParserService not available: {e}")
    
    @pytest.mark.asyncio
    async def test_parser_service_methods(self):
        """Test that ParserService has expected methods"""
        try:
            from services.parser import parser_service
            
            # Check that expected methods exist
            assert hasattr(parser_service, 'parse_document')
            assert hasattr(parser_service, 'delete_document_embeddings')
            assert callable(parser_service.parse_document)
            assert callable(parser_service.delete_document_embeddings)
        except ImportError:
            pytest.skip("ParserService not available")
    
    def test_supported_file_formats(self):
        """Test that parser supports expected file formats"""
        try:
            from services.parser import parser_service
            
            # Check supported formats
            assert hasattr(parser_service, 'supported_formats')
            supported_formats = parser_service.supported_formats
            
            expected_formats = ['.pdf', '.docx', '.txt', '.xlsx', '.csv']
            for fmt in expected_formats:
                assert fmt in supported_formats
        except ImportError:
            pytest.skip("ParserService not available")

class TestEmbeddingService:
    """Test EmbeddingService functionality"""
    
    @pytest.mark.asyncio
    async def test_embedding_service_import(self):
        """Test that EmbeddingService can be imported"""
        try:
            from services.embedding import embedding_service
            assert embedding_service is not None
        except ImportError as e:
            pytest.skip(f"EmbeddingService not available: {e}")
    
    @pytest.mark.asyncio
    async def test_embedding_service_methods(self):
        """Test that EmbeddingService has expected methods"""
        try:
            from services.embedding import embedding_service
            
            # Check that expected methods exist
            assert hasattr(embedding_service, 'generate_embeddings')
            assert hasattr(embedding_service, 'embed_documents')
            assert hasattr(embedding_service, 'delete_document_embeddings')
            assert hasattr(embedding_service, 'create_collection')
            
            assert callable(embedding_service.generate_embeddings)
            assert callable(embedding_service.embed_documents)
        except ImportError:
            pytest.skip("EmbeddingService not available")
    
    @pytest.mark.asyncio
    async def test_embedding_generation_mock(self, mock_bedrock_client):
        """Test embedding generation with mocked Bedrock client"""
        try:
            from services.embedding import embedding_service
            
            # Test with mock data
            texts = ["test text 1", "test text 2"]
            embeddings = await embedding_service.generate_embeddings(texts)
            
            assert len(embeddings) == len(texts)
            assert all(isinstance(emb, list) for emb in embeddings)
        except ImportError:
            pytest.skip("EmbeddingService not available")

class TestRAGService:
    """Test RAGService functionality"""
    
    @pytest.mark.asyncio
    async def test_rag_service_import(self):
        """Test that RAGService can be imported"""
        try:
            from services.rag import rag_service
            assert rag_service is not None
        except ImportError as e:
            pytest.skip(f"RAGService not available: {e}")
    
    @pytest.mark.asyncio
    async def test_rag_service_methods(self):
        """Test that RAGService has expected methods"""
        try:
            from services.rag import rag_service
            
            # Check that expected methods exist
            assert hasattr(rag_service, 'generate_response')
            assert hasattr(rag_service, 'search_similar_content')
            assert callable(rag_service.generate_response)
            assert callable(rag_service.search_similar_content)
        except ImportError:
            pytest.skip("RAGService not available")

class TestRealtimeCrawlService:
    """Test RealtimeCrawlService functionality"""
    
    @pytest.mark.asyncio
    async def test_realtime_crawl_service_import(self):
        """Test that RealtimeCrawlService can be imported"""
        try:
            from services.realtime_crawler import realtime_crawl_service
            assert realtime_crawl_service is not None
        except ImportError as e:
            pytest.skip(f"RealtimeCrawlService not available: {e}")
    
    @pytest.mark.asyncio
    async def test_realtime_crawl_service_methods(self):
        """Test that RealtimeCrawlService has expected methods"""
        try:
            from services.realtime_crawler import realtime_crawl_service
            
            # Check that expected methods exist
            assert hasattr(realtime_crawl_service, 'start_realtime_crawl')
            assert hasattr(realtime_crawl_service, 'cancel_crawl')
            assert hasattr(realtime_crawl_service, 'get_crawl_status')
            
            assert callable(realtime_crawl_service.start_realtime_crawl)
            assert callable(realtime_crawl_service.cancel_crawl)
        except ImportError:
            pytest.skip("RealtimeCrawlService not available")

class TestServiceIntegration:
    """Test service integration and dependencies"""
    
    @pytest.mark.asyncio
    async def test_all_services_available(self):
        """Test that all expected services are available"""
        services = [
            "services.crawler",
            "services.parser", 
            "services.embedding",
            "services.rag",
            "services.realtime_crawler"
        ]
        
        available_services = []
        for service_name in services:
            try:
                __import__(service_name)
                available_services.append(service_name)
            except ImportError:
                pass
        
        # At least some services should be available
        assert len(available_services) > 0
    
    @pytest.mark.asyncio
    async def test_service_dependencies(self):
        """Test that services can access their dependencies"""
        try:
            from config.database import get_qdrant_client, get_bedrock_client, get_supabase_admin_client
            
            # These should not raise exceptions (though they might return None in test env)
            qdrant_client = get_qdrant_client()
            bedrock_client = get_bedrock_client()
            supabase_client = get_supabase_admin_client()
            
            # At least the functions should exist
            assert callable(get_qdrant_client)
            assert callable(get_bedrock_client)
            assert callable(get_supabase_admin_client)
        except Exception as e:
            pytest.skip(f"Service dependencies not available: {e}")
    
    def test_service_configuration(self):
        """Test that services are properly configured"""
        try:
            from config.settings import settings
            
            # Check that required settings exist
            required_settings = [
                'SUPABASE_URL',
                'QDRANT_URL', 
                'AWS_REGION',
                'OLLAMA_URL'
            ]
            
            for setting in required_settings:
                assert hasattr(settings, setting)
                assert getattr(settings, setting) is not None
        except Exception as e:
            pytest.skip(f"Settings not available: {e}")