from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: str
    openai_api_key: str
    sonix_api_key: str
    pinecone_api_key: Optional[str] = None
    weaviate_url: Optional[str] = None
    weaviate_api_key: Optional[str] = None

    # Database
    database_url: str = "postgresql://user:password@localhost/knowledge_capture"
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "knowledge_capture"
    redis_url: str = "redis://localhost:6379"

    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # File Storage
    upload_dir: str = "uploads"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: list = [".txt", ".pdf", ".doc", ".docx"]

    # AI/LLM Settings
    default_model: str = "gpt-3.5-turbo"
    max_tokens: int = 2000
    temperature: float = 0.7

    # Application
    app_name: str = "Knowledge Capture MVP"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
