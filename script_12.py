# Create setup and deployment files
setup_script_content = """#!/usr/bin/env python3
\"\"\"
Setup script for Knowledge Capture MVP
\"\"\"

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    \"\"\"Run a shell command and handle errors\"\"\"
    print(f"\\n{description}...")
    try:
        subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in {description}: {e}")
        return False
    return True

def setup_database():
    \"\"\"Setup database and create tables\"\"\"
    print("\\n🗄️ Setting up database...")
    
    # Check if PostgreSQL is running
    try:
        subprocess.run("psql --version", shell=True, check=True, capture_output=True)
        print("✅ PostgreSQL found")
    except subprocess.CalledProcessError:
        print("❌ PostgreSQL not found. Please install PostgreSQL first.")
        return False
    
    # Create database (this might fail if database exists)
    print("Creating database...")
    subprocess.run("createdb knowledge_capture", shell=True, capture_output=True)
    
    return True

def setup_python_environment():
    \"\"\"Setup Python virtual environment and install requirements\"\"\"
    print("\\n🐍 Setting up Python environment...")
    
    # Create virtual environment
    if not Path("venv").exists():
        if not run_command("python3 -m venv venv", "Creating virtual environment"):
            return False
    
    # Activate and install requirements
    activate_cmd = ". venv/bin/activate" if os.name != 'nt' else "venv\\\\Scripts\\\\activate"
    pip_cmd = f"{activate_cmd} && pip install -r requirements.txt"
    
    if not run_command(pip_cmd, "Installing Python requirements"):
        return False
    
    return True

def setup_redis():
    \"\"\"Check Redis installation\"\"\"
    print("\\n🔴 Checking Redis...")
    
    try:
        subprocess.run("redis-cli ping", shell=True, check=True, capture_output=True)
        print("✅ Redis is running")
        return True
    except subprocess.CalledProcessError:
        print("❌ Redis not running. Please start Redis server.")
        print("Install Redis: https://redis.io/docs/getting-started/installation/")
        return False

def create_env_file():
    \"\"\"Create .env file from template\"\"\"
    print("\\n⚙️ Setting up environment configuration...")
    
    env_file = Path(".env")
    template_file = Path(".env.template")
    
    if not env_file.exists() and template_file.exists():
        # Copy template to .env
        with open(template_file, 'r') as template:
            content = template.read()
        
        with open(env_file, 'w') as env:
            env.write(content)
        
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your actual API keys and configuration!")
    else:
        print("✅ .env file already exists")
    
    return True

def main():
    \"\"\"Main setup function\"\"\"
    print("🚀 Setting up Knowledge Capture MVP...")
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    success = True
    
    # Setup steps
    success &= create_env_file()
    success &= setup_python_environment()
    success &= setup_database()
    success &= setup_redis()
    
    if success:
        print("\\n🎉 Setup completed successfully!")
        print("\\nNext steps:")
        print("1. Edit .env file with your API keys")
        print("2. Start the backend: python main.py")
        print("3. Start the frontend: streamlit run frontend/streamlit_app.py")
    else:
        print("\\n❌ Setup encountered errors. Please check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""

with open("knowledge_capture_mvp/setup.py", "w") as f:
    f.write(setup_script_content)

# Create Docker files
dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    postgresql-client \\
    redis-tools \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

with open("knowledge_capture_mvp/Dockerfile", "w") as f:
    f.write(dockerfile_content)

# Create docker-compose file
docker_compose_content = """version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/knowledge_capture
      - REDIS_URL=redis://redis:6379
      - MONGODB_URL=mongodb://mongo:27017
    depends_on:
      - db
      - redis
      - mongo
    volumes:
      - ./uploads:/app/uploads
      - ./.env:/app/.env

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "8501:8501"
    depends_on:
      - app
    environment:
      - API_BASE_URL=http://app:8000/api

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: knowledge_capture
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  mongo:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db

  # Optional: Vector database
  weaviate:
    image: semitechnologies/weaviate:1.21.8
    ports:
      - "8080:8080"
    environment:
      QUERY_DEFAULTS_LIMIT: 25
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
      DEFAULT_VECTORIZER_MODULE: 'none'
      ENABLE_MODULES: 'text2vec-openai,generative-openai'
    volumes:
      - weaviate_data:/var/lib/weaviate

volumes:
  postgres_data:
  redis_data:
  mongo_data:
  weaviate_data:
"""

with open("knowledge_capture_mvp/docker-compose.yml", "w") as f:
    f.write(docker_compose_content)

# Create frontend Dockerfile
frontend_dockerfile_content = """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend code
COPY frontend/ ./frontend/
COPY config/ ./config/

# Expose Streamlit port
EXPOSE 8501

# Command to run Streamlit
CMD ["streamlit", "run", "frontend/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
"""

with open("knowledge_capture_mvp/Dockerfile.frontend", "w") as f:
    f.write(frontend_dockerfile_content)

print("Setup and deployment files created!")
print("- setup.py")
print("- Dockerfile") 
print("- docker-compose.yml")
print("- Dockerfile.frontend")