# Create configuration files
config_content = """from pydantic_settings import BaseSettings
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
"""

with open("knowledge_capture_mvp/config/settings.py", "w") as f:
    f.write(config_content)

# Create .env template
env_template = """# API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
SONIX_API_KEY=your_sonix_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your_weaviate_api_key_here

# Database
DATABASE_URL=postgresql://user:password@localhost/knowledge_capture
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=knowledge_capture
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-super-secret-key-here-change-this
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application
DEBUG=False
HOST=0.0.0.0
PORT=8000
"""

with open("knowledge_capture_mvp/.env.template", "w") as f:
    f.write(env_template)

print("Configuration files created!")
print("- config/settings.py")
print("- .env.template")