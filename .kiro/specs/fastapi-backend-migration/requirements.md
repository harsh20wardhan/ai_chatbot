# Requirements Document

## Introduction

This feature involves migrating the existing Cloudflare Workers API (located in the `api/` folder) and consolidating all individual microservices (crawler, parser, embedding, RAG, realtime crawl) into a single unified FastAPI backend application. The migration will reuse existing business logic from the current services with minimal changes, adapting them to work within the FastAPI framework. The new backend will maintain the same functionality while providing better maintainability, easier deployment, and centralized service management.

## Requirements

### Requirement 1

**User Story:** As a system administrator, I want a single FastAPI backend that consolidates all services by migrating existing service logic, so that I can deploy and manage the entire backend infrastructure from one application.

#### Acceptance Criteria

1. WHEN the FastAPI application starts THEN it SHALL initialize all service modules by importing and adapting existing service logic from individual service folders
2. WHEN a request is made to any service endpoint THEN the system SHALL route it to the appropriate service handler using the migrated logic
3. WHEN the application is deployed THEN it SHALL require only one deployment process instead of multiple service deployments
4. IF any service fails THEN the system SHALL log the error with detailed context and continue serving other services

### Requirement 2

**User Story:** As a frontend developer, I want the FastAPI backend to provide the same API endpoints as the current system, so that the dashboard and widget can continue working without changes.

#### Acceptance Criteria

1. WHEN the dashboard makes API calls THEN the FastAPI backend SHALL respond with the same data structure and format as the current Cloudflare Workers
2. WHEN authentication is required THEN the system SHALL use Supabase authentication exactly as implemented currently
3. WHEN CORS requests are made THEN the system SHALL handle them with the same ALLOWED_ORIGIN configuration
4. IF an API endpoint is called THEN the response format SHALL match the existing API contract

### Requirement 3

**User Story:** As a developer, I want the FastAPI backend to use the same environment variables and external dependencies, so that configuration remains consistent.

#### Acceptance Criteria

1. WHEN the application starts THEN it SHALL read all environment variables from a .env file with the same variable names
2. WHEN connecting to Supabase THEN the system SHALL use SUPABASE_URL, SUPABASE_ANON_KEY, and SUPABASE_SERVICE_ROLE_KEY
3. WHEN connecting to Qdrant THEN the system SHALL use QDRANT_URL and QDRANT_API_KEY
4. WHEN connecting to external services THEN the system SHALL use the same AWS, Ollama, and database credentials
5. IF environment variables are missing THEN the system SHALL provide clear error messages

### Requirement 4

**User Story:** As a developer, I want all crawler functionality available as FastAPI endpoints by migrating existing crawler service logic, so that web crawling can be performed through the unified backend.

#### Acceptance Criteria

1. WHEN a crawl request is made THEN the system SHALL process URLs and extract content using the migrated logic from `crawler/crawler.py`
2. WHEN crawl results are ready THEN the system SHALL store them in the database using existing Supabase connection patterns
3. WHEN realtime crawling is requested THEN the system SHALL provide endpoints using migrated logic from `realtime_crawl_service.py`
4. IF crawling fails THEN the system SHALL return appropriate error responses with detailed logging for debugging

### Requirement 5

**User Story:** As a developer, I want all document parsing functionality available as FastAPI endpoints by migrating existing parser service logic, so that document processing can be performed through the unified backend.

#### Acceptance Criteria

1. WHEN a document is uploaded THEN the system SHALL parse it using the migrated logic from `parser/parser.py`
2. WHEN parsing is complete THEN the system SHALL return structured content data in the same format as the current parser service
3. WHEN different document types are processed THEN the system SHALL handle formats using the existing parser implementation
4. IF parsing fails THEN the system SHALL return error responses with specific failure reasons and detailed logging

### Requirement 6

**User Story:** As a developer, I want all embedding functionality available as FastAPI endpoints by migrating existing embedding service logic, so that text embeddings can be generated through the unified backend.

#### Acceptance Criteria

1. WHEN text embedding is requested THEN the system SHALL generate embeddings using the migrated logic from `embedding_service/embedding_service.py`
2. WHEN embeddings are generated THEN the system SHALL store them in Qdrant using existing connection patterns
3. WHEN embedding search is performed THEN the system SHALL query Qdrant using migrated logic from `embedding_service/search.py`
4. IF embedding generation fails THEN the system SHALL return error responses with diagnostic information and comprehensive logging

### Requirement 7

**User Story:** As a developer, I want all RAG functionality available as FastAPI endpoints by migrating existing RAG service logic, so that question-answering can be performed through the unified backend.

#### Acceptance Criteria

1. WHEN a RAG query is made THEN the system SHALL retrieve relevant context and generate answers using migrated logic from `rag/rag_answer.py`
2. WHEN connecting to Ollama THEN the system SHALL use the configured OLLAMA_URL and OLLAMA_MODEL with existing connection patterns
3. WHEN RAG processing is complete THEN the system SHALL return structured answers with source references in the same format as current implementation
4. IF RAG processing fails THEN the system SHALL return error responses with context about the failure and detailed logging for debugging

### Requirement 8

**User Story:** As a developer, I want proper authentication and authorization, so that the FastAPI backend maintains the same security model as the current system.

#### Acceptance Criteria

1. WHEN protected endpoints are accessed THEN the system SHALL validate Supabase JWT tokens
2. WHEN user authentication is required THEN the system SHALL verify tokens using SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY
3. WHEN unauthorized access is attempted THEN the system SHALL return 401 or 403 status codes
4. IF authentication fails THEN the system SHALL provide clear error messages without exposing sensitive information

### Requirement 9

**User Story:** As a developer, I want comprehensive error handling and logging throughout all API endpoints, so that issues can be diagnosed and resolved quickly during development and production.

#### Acceptance Criteria

1. WHEN any API endpoint is called THEN the system SHALL log the request details including method, path, and parameters
2. WHEN errors occur THEN the system SHALL log them with appropriate severity levels, stack traces, and contextual information
3. WHEN API requests fail THEN the system SHALL return structured error responses with error codes and log the failure details
4. WHEN services are unavailable THEN the system SHALL provide meaningful error messages and log connection failures
5. IF critical errors occur THEN the system SHALL continue serving other endpoints when possible and log recovery attempts
6. WHEN debugging is needed THEN logs SHALL provide sufficient detail to trace request flow through all service layers

### Requirement 10

**User Story:** As a developer, I want the FastAPI backend to replicate all Cloudflare Workers API functionality by migrating existing API logic, so that the frontend applications continue working without modification.

#### Acceptance Criteria

1. WHEN migrating API endpoints THEN the system SHALL copy and adapt the logic from `api/src/` folder to FastAPI route handlers
2. WHEN API responses are generated THEN they SHALL maintain the same JSON structure and status codes as the Cloudflare Workers implementation
3. WHEN authentication middleware is needed THEN it SHALL be migrated from the existing Cloudflare Workers auth patterns
4. IF API behavior differs from the original THEN the system SHALL log the differences and maintain backward compatibility

### Requirement 11

**User Story:** As a developer, I want a maintained requirements.txt file, so that all dependencies are properly tracked and can be installed consistently.

#### Acceptance Criteria

1. WHEN new libraries are added THEN they SHALL be added to requirements.txt with appropriate version constraints
2. WHEN the application is deployed THEN all dependencies SHALL be installable from requirements.txt
3. WHEN dependencies are updated THEN the requirements.txt SHALL reflect the current versions
4. IF dependency conflicts exist THEN they SHALL be resolved and documented