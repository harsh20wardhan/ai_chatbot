# Implementation Plan

- [x] 1. Set up FastAPI project structure and core configuration

  - Create the main FastAPI application directory structure
  - Set up environment configuration using Pydantic BaseSettings
  - Create database connection management with connection pooling
  - Initialize shared clients (Qdrant, Bedrock) as singletons
  - Create comprehensive logging configuration
  - Set up requirements.txt with all necessary dependencies
  - _Requirements: 1.1, 3.1, 3.2, 3.3, 9.1, 9.2, 11.1, 11.2_

- [ ] 2. Implement core middleware and authentication
- [x] 2.1 Create CORS middleware matching current configuration

  - Migrate CORS handling from Cloudflare Workers to FastAPI middleware
  - Ensure ALLOWED_ORIGIN environment variable is respected
  - Test preflight OPTIONS requests work correctly
  - _Requirements: 2.1, 2.3, 3.4_

- [x] 2.2 Implement Supabase authentication middleware

  - Create FastAPI dependency for JWT token validation
  - Migrate authentication logic from `api/src/middleware/auth.js`
  - Support both SUPABASE_ANON_KEY and SUPABASE_SERVICE_ROLE_KEY validation
  - Extract user context and make it available to route handlers
  - Implement proper error responses for unauthorized access
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 10.1, 10.2_

- [ ] 3. Migrate service layer business logic
- [x] 3.1 Implement CrawlerService class

  - Migrate logic from `crawler_service.py` and `crawler/crawler.py`
  - Implement `crawl_website()` method with same functionality
  - Implement `cancel_crawl()` method
  - Add comprehensive logging for debugging crawl operations
  - Ensure database integration matches current behavior
  - _Requirements: 4.1, 4.2, 9.1, 9.6, 10.1_

- [x] 3.2 Implement ParserService class



  - Migrate logic from `parser_service.py` and `parser/parser.py`
  - Implement document parsing for PDF, DOCX, TXT, Excel formats
  - Migrate text chunking functionality
  - Implement database storage for document chunks
  - Integrate with Supabase storage for file downloads
  - Add embedding generation and Qdrant storage
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 9.1, 9.6, 10.1_

- [x] 3.3 Implement EmbeddingService class



  - Migrate logic from `embedding_service.py` and `embedding_service/`
  - Implement Bedrock integration for embedding generation
  - Implement Qdrant collection management and vector storage
  - Migrate embedding job processing functionality
  - Add methods for deleting embeddings by document or collection
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 9.1, 9.6, 10.1_

- [x] 3.4 Implement RAGService class

  - Migrate logic from `rag_service.py` and `rag/rag_answer.py`
  - Implement query embedding and vector search functionality
  - Integrate with Ollama for answer generation
  - Migrate chat history formatting and context assembly
  - Implement response filtering to remove thinking tags
  - Add comprehensive logging for RAG pipeline debugging
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 9.1, 9.6, 10.1_

- [x] 3.5 Implement RealtimeCrawlService class



  - Migrate logic from `realtime_crawl_service.py`
  - Implement realtime crawling with WebSocket support
  - Migrate page embedding functionality for realtime processing
  - Implement database operations for crawled pages and embedding chunks
  - Add proper error handling and status updates
  - _Requirements: 4.3, 9.1, 9.6, 10.1_

- [x] 4. Create Pydantic models for request/response validation

  - Define all request and response schemas using Pydantic
  - Ensure models match current API contracts exactly
  - Add proper validation rules and error messages
  - Create models for authentication, bots, crawling, documents, chat, and admin endpoints
  - _Requirements: 2.1, 2.2, 9.3, 10.2, 10.3_

- [ ] 5. Implement API routers with migrated endpoint logic
- [x] 5.1 Create authentication router

  - Migrate endpoints from `api/src/handlers/auth.js`
  - Implement register, login, logout, getUser, changePassword endpoints
  - Ensure response formats match current Cloudflare Workers API
  - Add proper error handling and logging
  - _Requirements: 2.1, 2.2, 8.1, 8.2, 9.1, 9.3, 10.1, 10.2_

- [x] 5.2 Create bot management router



  - Migrate endpoints from `api/src/handlers/bots.js`
  - Implement CRUD operations for bots with authentication
  - Ensure Qdrant collection creation matches current behavior
  - Add proper validation and error responses
  - _Requirements: 2.1, 2.2, 8.1, 9.1, 9.3, 10.1, 10.2_

- [x] 5.3 Create crawling router



  - Migrate endpoints from `api/src/handlers/crawl.js` and `api/src/handlers/realtime_crawl.js`
  - Implement website crawling endpoints with job management
  - Implement realtime crawling endpoints with WebSocket support
  - Ensure database operations and status updates work correctly
  - Add comprehensive logging for crawl operations
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 9.1, 9.6, 10.1, 10.2_

- [x] 5.4 Create document management router



  - Migrate endpoints from `api/src/handlers/documents.js`
  - Implement document upload, retrieval, and deletion endpoints
  - Integrate with ParserService for document processing
  - Ensure Supabase storage integration works correctly
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 9.1, 9.3, 10.1, 10.2_

- [x] 5.5 Create embedding router





  - Migrate endpoints from `api/src/handlers/embeddings.js`
  - Implement embedding generation and management endpoints
  - Integrate with EmbeddingService for processing
  - Add proper job status tracking and error handling
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 9.1, 9.3, 10.1, 10.2_

- [x] 5.6 Create chat router


  - Migrate endpoints from `api/src/handlers/chat.js`
  - Implement RAG chat processing with conversation management
  - Integrate with RAGService for answer generation
  - Ensure response format matches current API exactly
  - Add proper error handling for RAG pipeline failures
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 9.1, 9.3, 10.1, 10.2_

- [x] 5.7 Create admin and analytics routers



  - Migrate endpoints from `api/src/handlers/admin.js` and `api/src/handlers/analytics.js`
  - Implement admin statistics and logging endpoints
  - Implement analytics endpoints for bot statistics
  - Ensure proper authentication for admin endpoints
  - _Requirements: 2.1, 8.1, 9.1, 9.3, 10.1, 10.2_

- [x] 5.8 Create widget router



  - Migrate endpoints from `api/src/handlers/widget.js`
  - Implement widget configuration endpoints
  - Ensure public and authenticated endpoints work correctly
  - _Requirements: 2.1, 8.1, 9.1, 9.3, 10.1, 10.2_

- [x] 6. Set up comprehensive error handling and logging




  - Implement global exception handlers for different error types
  - Create structured logging with request correlation IDs
  - Add performance logging for response time tracking
  - Implement proper error response formatting matching current API
  - Add health check endpoints for all dependencies
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [x] 7. Create main FastAPI application and integrate all components



  - Set up main.py with FastAPI app initialization
  - Register all routers with proper prefixes
  - Configure CORS middleware globally
  - Add startup and shutdown event handlers
  - Implement health check endpoint
  - Test that all endpoints are accessible and return expected responses
  - _Requirements: 1.1, 1.2, 1.3, 2.1, 2.3, 10.1, 10.2, 10.3_

- [x] 8. Create environment configuration file



  - Copy all environment variables from existing .env file
  - Ensure all variable names match exactly as specified
  - Validate that all required environment variables are present
  - Test database and external service connections
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 9. Test API compatibility and functionality



  - Test all endpoints return the same response format as current Cloudflare Workers API
  - Verify authentication works with existing Supabase configuration
  - Test database operations create the same data structures
  - Verify external service integrations (Qdrant, Bedrock, Ollama) work correctly
  - Test error handling returns appropriate status codes and messages
  - _Requirements: 2.1, 2.2, 8.1, 8.2, 9.3, 10.2, 10.3, 10.4_

- [x] 10. Update requirements.txt with all dependencies


  - Add FastAPI and all required dependencies
  - Include all libraries used by migrated services (boto3, qdrant-client, etc.)
  - Specify appropriate version constraints
  - Test that all dependencies install correctly
  - _Requirements: 11.1, 11.2, 11.3, 11.4_
