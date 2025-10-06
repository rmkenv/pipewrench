
"""Application settings and configuration."""
from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    sonix_api_key: str = ""
    pinecone_api_key: Optional[str] = None
    weaviate_url: Optional[str] = None
    weaviate_api_key: Optional[str] = None

    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/pipewrench"
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "pipewrench"
    redis_url: str = "redis://localhost:6379"

    # Security
    secret_key: str = "change-this-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # File Storage
    upload_dir: str = "uploads"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: List[str] = [".txt", ".pdf", ".doc", ".docx", ".mp3", ".wav", ".m4a"]

    # AI/LLM Settings
    default_model: str = "gpt-4"
    max_tokens: int = 2000
    temperature: float = 0.7

    # Application
    app_name: str = "Pipewrench Knowledge Capture"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    allowed_origins: str = "http://localhost:3000,http://localhost:8501"
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"

    class Config:
        env_file = ".env"
        case_sensitive = False
        
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    def ensure_directories(self):
        """Ensure required directories exist."""
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.log_file).parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
