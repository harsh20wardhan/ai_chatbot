"""
Application Settings

Environment configuration using Pydantic BaseSettings for type safety
and automatic environment variable loading.
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security settings
    ALLOWED_HOSTS: str = "*"
    
    # CORS settings
    ALLOWED_ORIGINS: str = "*"
    
    @property
    def ALLOWED_ORIGINS_LIST(self) -> List[str]:
        """Convert ALLOWED_ORIGINS to list for CORS middleware"""
        if self.ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]
    
    # Supabase configuration
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    
    # Supabase Database configuration
    SUPABASE_DB_HOST: str
    SUPABASE_DB_NAME: str = "postgres"
    SUPABASE_DB_USER: str
    SUPABASE_DB_PASSWORD: str
    SUPABASE_DB_PORT: int = 5432
    
    # Qdrant configuration
    QDRANT_URL: str
    QDRANT_API_KEY: str
    
    # AWS configuration
    AWS_REGION: str = "us-west-2"
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    
    # Bedrock model configuration
    BEDROCK_RAG_MODEL: str = "openai.gpt-oss-20b-1:0"
    BEDROCK_EMBEDDING_MODEL: str = "amazon.titan-embed-text-v2:0"
    
    # Performance & Monitoring settings
    RATE_LIMIT_PER_MINUTE: int = 60
    MAX_REQUEST_SIZE: int = 50 * 1024 * 1024  # 50MB
    SLOW_REQUEST_THRESHOLD: float = 1.0  # seconds
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    
    # Service keys (for internal authentication if needed)
    CRAWLER_SERVICE_KEY: str = "your-crawler-secret-key"
    PARSER_SERVICE_KEY: str = "your-parser-secret-key"
    EMBEDDINGS_SERVICE_KEY: str = "your-embedding-secret-key"
    RAG_SERVICE_KEY: str = "your-rag-secret-key"
    REALTIME_CRAWL_SERVICE_KEY: str = "your-secret-key"
    
    # Legacy service URLs (not used in unified backend but kept for reference)
    CRAWLER_SERVICE_URL: str = "http://localhost:8001"
    PARSER_SERVICE_URL: str = "http://localhost:8002"
    EMBEDDINGS_SERVICE_URL: str = "http://localhost:8003"
    RAG_SERVICE_URL: str = "http://localhost:8004"
    REALTIME_CRAWL_SERVICE_URL: str = "http://localhost:8005"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from environment

# Global settings instance
settings = Settings()

# Validate required settings on import
def validate_settings():
    """Validate that all required settings are present"""
    required_settings = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY", 
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_DB_HOST",
        "SUPABASE_DB_USER",
        "SUPABASE_DB_PASSWORD",
        "QDRANT_URL",
        "QDRANT_API_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY"
    ]
    
    missing_settings = []
    for setting in required_settings:
        if not getattr(settings, setting, None):
            missing_settings.append(setting)
    
    if missing_settings:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_settings)}")

# Validate settings on import
validate_settings()