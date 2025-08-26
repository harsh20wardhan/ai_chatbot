"""
Pydantic Models for Request/Response Validation

Defines all request and response schemas to ensure API contracts match
the current Cloudflare Workers implementation exactly.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum

# Base models
class BaseResponse(BaseModel):
    """Base response model with common fields"""
    pass

class ErrorResponse(BaseModel):
    """Standard error response format"""
    error: str
    details: Optional[str] = None
    correlation_id: Optional[str] = None

class SuccessResponse(BaseModel):
    """Standard success response format"""
    message: str
    data: Optional[Dict[str, Any]] = None

# Authentication models
class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str = Field(..., min_length=6)

class RegisterRequest(BaseModel):
    """Registration request model"""
    email: EmailStr
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

class ChangePasswordRequest(BaseModel):
    """Change password request model"""
    current_password: str
    new_password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v

class AuthResponse(BaseModel):
    """Authentication response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class UserResponse(BaseModel):
    """User information response model"""
    id: str
    email: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    user_metadata: Dict[str, Any] = {}
    app_metadata: Dict[str, Any] = {}

# Bot management models
class CreateBotRequest(BaseModel):
    """Create bot request model"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    website_url: Optional[str] = None
    
    @validator('website_url')
    def validate_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

class UpdateBotRequest(BaseModel):
    """Update bot request model"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    website_url: Optional[str] = None
    
    @validator('website_url')
    def validate_url(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

class BotResponse(BaseModel):
    """Bot response model"""
    id: str
    name: str
    description: Optional[str]
    website_url: Optional[str]
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

class BotWithStatsResponse(BaseModel):
    """Bot response model with additional statistics"""
    id: str
    name: str
    description: Optional[str]
    website_url: Optional[str]
    user_id: str
    created_at: str  # ISO format string for frontend compatibility
    updated_at: Optional[str] = None  # ISO format string for frontend compatibility
    messages_count: int = 0
    documents_count: int = 0
    status: str = "active"

class BotListResponse(BaseModel):
    """Bot list response model"""
    bots: List[BotWithStatsResponse]
    total: int

# Crawling models
class CrawlStatus(str, Enum):
    """Crawl job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class CrawlRequest(BaseModel):
    """Website crawl request model"""
    url: str = Field(..., pattern=r'^https?://[^\s/$.?#].[^\s]*$')
    max_pages: int = Field(3, ge=1, le=10)  # Changed from max_depth to match dashboard
    exclude_patterns: List[str] = Field(default_factory=list)
    bot_id: str

class RealtimeCrawlRequest(BaseModel):
    """Realtime crawl request model"""
    url: str = Field(..., pattern=r'^https?://[^\s/$.?#].[^\s]*$')
    max_pages: int = Field(3, ge=1, le=20)  # Changed from max_depth to match dashboard
    exclude_patterns: List[str] = Field(default_factory=list)
    bot_id: str
    # job_id is optional - will be generated if not provided

class CrawlStatusResponse(BaseModel):
    """Crawl status response model"""
    job_id: str
    status: CrawlStatus
    pages_crawled: int = 0
    total_pages: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

class CrawlJobResponse(BaseModel):
    """Crawl job response model for job creation"""
    job_id: str
    message: str
    status: str

class RealtimeCrawlResponse(BaseModel):
    """Realtime crawl response model"""
    job_id: str
    session_id: str
    message: str
    websocket_url: str

class CrawlJobDetailResponse(BaseModel):
    """Detailed crawl job response model"""
    id: str
    bot_id: str
    url: str
    max_depth: int
    exclude_patterns: List[str]
    status: CrawlStatus
    pages_crawled: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

class CrawlJobListResponse(BaseModel):
    """Crawl job list response model"""
    jobs: List[CrawlJobDetailResponse]
    total: int

class CrawledPageResponse(BaseModel):
    """Crawled page response model"""
    id: str
    url: str
    title: str
    content_length: int
    status: str
    created_at: datetime
    embedded_at: Optional[datetime] = None

class CrawledPageListResponse(BaseModel):
    """Crawled page list response model"""
    pages: List[CrawledPageResponse]
    total: int

# Document models
class DocumentStatus(str, Enum):
    """Document processing status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"

class DocumentResponse(BaseModel):
    """Document response model"""
    id: str
    bot_id: str
    filename: str
    file_type: str
    file_size: int
    status: DocumentStatus
    created_at: datetime
    processed_at: Optional[datetime] = None
    error: Optional[str] = None

class DocumentListResponse(BaseModel):
    """Document list response model"""
    documents: List[DocumentResponse]
    total: int

class DocumentUploadResponse(BaseModel):
    """Document upload response model"""
    document_id: str
    filename: str
    file_size: int
    status: DocumentStatus
    message: str

# Embedding models
class EmbeddingJobStatus(str, Enum):
    """Embedding job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class GenerateEmbeddingsRequest(BaseModel):
    """Generate embeddings request model"""
    bot_id: str
    document_ids: List[str] = Field(..., min_items=1)

class EmbeddingJobResponse(BaseModel):
    """Embedding job response model"""
    job_id: str
    message: str
    status: str

class EmbeddingStatusResponse(BaseModel):
    """Embedding job status response model"""
    job_id: str
    status: EmbeddingJobStatus
    documents_processed: int = 0
    total_documents: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

class DeleteEmbeddingsRequest(BaseModel):
    """Delete embeddings request model"""
    bot_id: str

# Vector database models
class CollectionResponse(BaseModel):
    """Vector collection response model"""
    name: str
    vectors_count: int
    indexed_vectors_count: int
    points_count: int
    segments_count: int
    status: str

class CollectionListResponse(BaseModel):
    """Collection list response model"""
    collections: List[CollectionResponse]

class CreateCollectionRequest(BaseModel):
    """Create collection request model"""
    name: str
    size: int = Field(1024, ge=1, le=4096)
    distance: str = Field("Cosine", pattern=r'^(Cosine|Euclidean|Dot)$')

# Chat models
class ChatMessage(BaseModel):
    """Chat message model"""
    role: str = Field(..., pattern=r'^(user|assistant)$')
    content: str

class ChatRequest(BaseModel):
    """Chat request model"""
    query: str = Field(..., min_length=1, max_length=2000)
    bot_id: str
    conversation_id: Optional[str] = None
    message_history: List[ChatMessage] = Field(default_factory=list)

class ChatSource(BaseModel):
    """Chat response source model"""
    index: int
    score: float
    text: str
    document_id: str

class ChatResponse(BaseModel):
    """Chat response model"""
    answer: str
    answer_text: str
    answer_html: str
    sources: List[ChatSource]
    tokens_used: int
    conversation_id: str
    error: Optional[str] = None

class ConversationResponse(BaseModel):
    """Conversation response model"""
    id: str
    bot_id: str
    messages: List[ChatMessage]
    created_at: datetime
    updated_at: Optional[datetime] = None

class ConversationListResponse(BaseModel):
    """Conversation list response model"""
    conversations: List[ConversationResponse]
    total: int

# Admin models
class AdminStatsResponse(BaseModel):
    """Admin statistics response model"""
    total_users: int
    total_bots: int
    total_documents: int
    total_conversations: int
    total_crawl_jobs: int
    active_crawl_jobs: int

class LogEntry(BaseModel):
    """Log entry model"""
    timestamp: datetime
    level: str
    message: str
    service: Optional[str] = None
    correlation_id: Optional[str] = None

class LogsResponse(BaseModel):
    """Logs response model"""
    logs: List[LogEntry]
    total: int

class JobEntry(BaseModel):
    """Job entry model"""
    id: str
    type: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    error: Optional[str] = None

class JobsResponse(BaseModel):
    """Jobs response model"""
    jobs: List[JobEntry]
    total: int

# Analytics models
class BotStatsResponse(BaseModel):
    """Bot statistics response model"""
    bot_id: str
    total_conversations: int
    total_messages: int
    total_documents: int
    total_crawled_pages: int
    avg_response_time: float
    last_activity: Optional[datetime] = None

# Widget models
class WidgetConfig(BaseModel):
    """Widget configuration model"""
    bot_id: str
    title: str = "AI Assistant"
    subtitle: str = "How can I help you today?"
    primary_color: str = "#007bff"
    text_color: str = "#333333"
    background_color: str = "#ffffff"
    position: str = Field("bottom-right", pattern=r'^(bottom-right|bottom-left|top-right|top-left)$')
    enabled: bool = True

class UpdateWidgetConfigRequest(BaseModel):
    """Update widget configuration request model"""
    title: Optional[str] = None
    subtitle: Optional[str] = None
    primary_color: Optional[str] = Field(None, pattern=r'^#[0-9a-fA-F]{6}$')
    text_color: Optional[str] = Field(None, pattern=r'^#[0-9a-fA-F]{6}$')
    background_color: Optional[str] = Field(None, pattern=r'^#[0-9a-fA-F]{6}$')
    position: Optional[str] = Field(None, pattern=r'^(bottom-right|bottom-left|top-right|top-left)$')
    enabled: Optional[bool] = None

class WidgetConfigResponse(BaseModel):
    """Widget configuration response model"""
    config: WidgetConfig

# Health check models
class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str
    service: str
    version: str
    timestamp: float
    dependencies: Optional[Dict[str, str]] = None