# Design Document

## Overview

This design outlines the migration from the current distributed architecture (Cloudflare Workers + multiple Flask microservices) to a unified FastAPI backend. The new architecture will consolidate all services into a single FastAPI application while maintaining the same API contracts and functionality.

### Current Architecture
- **Cloudflare Workers API**: Main API gateway with handlers for different services
- **Individual Flask Services**: 
  - Crawler Service (port 8001)
  - Parser Service (port 8002) 
  - Embedding Service (port 8003)
  - RAG Service (port 8004)
  - Realtime Crawl Service (port 8005)

### Target Architecture
- **Single FastAPI Application**: Unified backend serving all endpoints
- **Service Modules**: Internal service classes replacing external Flask services
- **Shared Dependencies**: Common database connections, Qdrant client, AWS Bedrock client

## Architecture

### Application Structure
```
fastapi_backend/
├── main.py                 # FastAPI application entry point
├── config/
│   ├── __init__.py
│   ├── settings.py         # Environment configuration
│   └── database.py         # Database connection management
├── middleware/
│   ├── __init__.py
│   ├── cors.py            # CORS middleware
│   └── auth.py            # Supabase authentication middleware
├── services/
│   ├── __init__.py
│   ├── crawler.py         # Migrated crawler logic
│   ├── parser.py          # Migrated parser logic
│   ├── embedding.py       # Migrated embedding logic
│   ├── rag.py             # Migrated RAG logic
│   └── realtime_crawl.py  # Migrated realtime crawl logic
├── routers/
│   ├── __init__.py
│   ├── auth.py            # Authentication endpoints
│   ├── bots.py            # Bot management endpoints
│   ├── crawl.py           # Crawling endpoints
│   ├── documents.py       # Document management endpoints
│   ├── embeddings.py      # Embedding endpoints
│   ├── chat.py            # RAG chat endpoints
│   ├── admin.py           # Admin endpoints
│   ├── analytics.py       # Analytics endpoints
│   └── widget.py          # Widget endpoints
├── models/
│   ├── __init__.py
│   └── schemas.py         # Pydantic models for request/response
├── utils/
│   ├── __init__.py
│   ├── logging.py         # Centralized logging configuration
│   └── helpers.py         # Common utility functions
└── requirements.txt       # Python dependencies
```

## Components and Interfaces

### 1. FastAPI Application (main.py)
- **Purpose**: Application entry point and router registration
- **Dependencies**: All routers, middleware, and global configuration
- **Key Features**:
  - CORS configuration matching current ALLOWED_ORIGIN
  - Global exception handling with detailed logging
  - Health check endpoint
  - Startup/shutdown event handlers for resource initialization

### 2. Configuration Management (config/)
- **settings.py**: Environment variable management using Pydantic BaseSettings
- **database.py**: Database connection pooling and management
- **Key Features**:
  - Type-safe environment variable loading
  - Connection pooling for PostgreSQL (Supabase)
  - Singleton pattern for shared resources (Qdrant client, Bedrock client)

### 3. Authentication Middleware (middleware/auth.py)
- **Purpose**: Migrate Supabase JWT validation from Cloudflare Workers
- **Implementation**: FastAPI dependency injection for protected routes
- **Key Features**:
  - JWT token validation using SUPABASE_ANON_KEY and SUPABASE_SERVICE_ROLE_KEY
  - User context extraction and injection
  - Consistent error responses matching current API

### 4. Service Layer (services/)
Each service module will encapsulate the business logic from the corresponding Flask service:

#### CrawlerService (services/crawler.py)
- **Migrated from**: `crawler_service.py` and `crawler/crawler.py`
- **Key Methods**:
  - `crawl_website(url, max_depth, exclude_patterns)` 
  - `cancel_crawl(job_id)`
- **Dependencies**: Database connection, logging

#### ParserService (services/parser.py)
- **Migrated from**: `parser_service.py` and `parser/parser.py`
- **Key Methods**:
  - `parse_document(document_id, file_path, file_type)`
  - `chunk_text(text, chunk_size, overlap)`
  - `store_document_chunks(document_id, bot_id, user_id, chunks)`
- **Dependencies**: Database connection, Supabase storage client, Qdrant client, Bedrock client

#### EmbeddingService (services/embedding.py)
- **Migrated from**: `embedding_service.py` and `embedding_service/`
- **Key Methods**:
  - `generate_embeddings(texts)`
  - `embed_documents(job_id, bot_id, document_ids)`
  - `delete_document_embeddings(document_id, bot_id)`
- **Dependencies**: Qdrant client, Bedrock client

#### RAGService (services/rag.py)
- **Migrated from**: `rag_service.py` and `rag/rag_answer.py`
- **Key Methods**:
  - `process_chat(query, bot_id, conversation_id, message_history)`
  - `search_relevant_documents(query_embedding, bot_id)`
  - `generate_answer(context, query, chat_history)`
- **Dependencies**: Qdrant client, Bedrock client, Ollama client

#### RealtimeCrawlService (services/realtime_crawl.py)
- **Migrated from**: `realtime_crawl_service.py`
- **Key Methods**:
  - `start_realtime_crawl(url, max_depth, exclude_patterns, bot_id, job_id)`
  - `crawl_website_realtime(base_url, max_pages, exclude_patterns, session_id, bot_id, job_id)`
  - `embed_page_realtime(page_id, text, bot_id, session_id)`
- **Dependencies**: Database connection, Qdrant client, Bedrock client, WebSocket support

### 5. API Routers (routers/)
Each router will migrate the corresponding handlers from the Cloudflare Workers API:

#### Authentication Router (routers/auth.py)
- **Migrated from**: `api/src/handlers/auth.js`
- **Endpoints**:
  - `POST /api/auth/register`
  - `POST /api/auth/login`
  - `POST /api/auth/logout`
  - `GET /api/auth/user`
  - `POST /api/auth/change-password`

#### Bot Management Router (routers/bots.py)
- **Migrated from**: `api/src/handlers/bots.js`
- **Endpoints**:
  - `GET /api/bots`
  - `POST /api/bots`
  - `GET /api/bots/{bot_id}`
  - `PUT /api/bots/{bot_id}`
  - `DELETE /api/bots/{bot_id}`

#### Crawling Router (routers/crawl.py)
- **Migrated from**: `api/src/handlers/crawl.js` and `api/src/handlers/realtime_crawl.js`
- **Endpoints**:
  - `POST /api/crawl/website`
  - `GET /api/crawl/status/{job_id}`
  - `GET /api/crawl/jobs`
  - `DELETE /api/crawl/job/{job_id}`
  - `POST /api/realtime-crawl/start`
  - `GET /api/realtime-crawl/status/{job_id}`

#### Document Management Router (routers/documents.py)
- **Migrated from**: `api/src/handlers/documents.js`
- **Endpoints**:
  - `POST /api/documents/upload`
  - `GET /api/documents`
  - `GET /api/documents/{document_id}`
  - `DELETE /api/documents/{document_id}`

#### Chat Router (routers/chat.py)
- **Migrated from**: `api/src/handlers/chat.js`
- **Endpoints**:
  - `POST /api/chat`
  - `GET /api/chat/conversations`
  - `GET /api/chat/conversations/{conversation_id}`

## Data Models

### Request/Response Schemas (models/schemas.py)
Using Pydantic models for type safety and validation:

```python
# Authentication
class LoginRequest(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime

# Bot Management
class CreateBotRequest(BaseModel):
    name: str
    description: Optional[str] = None
    website_url: Optional[str] = None

class BotResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    website_url: Optional[str]
    user_id: str
    created_at: datetime

# Crawling
class CrawlRequest(BaseModel):
    url: str
    max_depth: int = 3
    exclude_patterns: List[str] = []

class CrawlStatusResponse(BaseModel):
    job_id: str
    status: str
    pages_crawled: int
    total_pages: Optional[int]

# Chat
class ChatRequest(BaseModel):
    query: str
    bot_id: str
    conversation_id: Optional[str] = None
    message_history: List[Dict[str, str]] = []

class ChatResponse(BaseModel):
    answer: str
    answer_text: str
    answer_html: str
    sources: List[Dict[str, Any]]
    tokens_used: int
    conversation_id: str
```

## Error Handling

### Global Exception Handler
- **HTTP Exceptions**: Return structured JSON responses with appropriate status codes
- **Validation Errors**: Return detailed field-level validation messages
- **Service Errors**: Log full stack traces while returning sanitized error messages
- **Database Errors**: Handle connection failures and transaction rollbacks gracefully

### Logging Strategy
- **Request Logging**: Log all incoming requests with method, path, parameters, and user context
- **Service Logging**: Detailed logging within each service method for debugging
- **Error Logging**: Full exception details with stack traces for troubleshooting
- **Performance Logging**: Track response times for optimization

## Testing Strategy

### Unit Tests
- **Service Layer**: Test each service method with mocked dependencies
- **Router Layer**: Test endpoint behavior with mocked services
- **Middleware**: Test authentication and CORS functionality

### Integration Tests
- **Database Integration**: Test database operations with test database
- **External Services**: Test Qdrant and Bedrock integration with test environments
- **End-to-End**: Test complete request flows from API to database

### Migration Validation
- **API Contract Testing**: Ensure all endpoints return the same response format as current implementation
- **Data Consistency**: Verify that migrated services produce identical results
- **Performance Testing**: Ensure the unified backend meets or exceeds current performance

## Deployment Considerations

### Environment Configuration
- **Development**: Local development with Docker Compose for dependencies
- **Staging**: Cloud deployment with managed services (Supabase, Qdrant Cloud)
- **Production**: Scalable deployment with proper monitoring and logging

### Resource Management
- **Connection Pooling**: Efficient database connection management
- **Memory Management**: Proper cleanup of large objects (embeddings, documents)
- **Async Operations**: Use FastAPI's async capabilities for I/O-bound operations

### Monitoring and Observability
- **Health Checks**: Comprehensive health endpoints for all dependencies
- **Metrics**: Request counts, response times, error rates
- **Logging**: Structured logging with correlation IDs for request tracing