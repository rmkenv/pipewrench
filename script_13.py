# Create additional utility files and scripts

# Create README.md
readme_content = """# Knowledge Capture MVP

A comprehensive system for capturing, preserving, and operationalizing organizational knowledge through AI-powered document ingestion, employee interviews, and chatbot training.

## 🚀 Features

- **Document Management**: Upload and process various document types (PDF, DOC, TXT)
- **AI-Powered Question Generation**: Generate tailored interview questions using Anthropic API
- **Audio Transcription**: Automatic transcription using Sonix API
- **Knowledge Report Generation**: AI-generated comprehensive reports for each role
- **RAG-Powered Chatbot**: Chat with organizational knowledge base
- **Chat with Files**: Upload and chat with individual documents
- **Ongoing Maintenance**: Automated system maintenance and content review
- **Security**: Role-based access control, authentication, and audit trails

## 🏗️ Architecture

- **Backend**: FastAPI with Python
- **Frontend**: Streamlit web interface
- **Database**: PostgreSQL (main), MongoDB (documents), Redis (caching)
- **Vector Database**: Pinecone or Weaviate for RAG
- **AI Services**: Anthropic Claude, OpenAI GPT, Sonix transcription
- **Authentication**: JWT-based with role-based access control

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- MongoDB 7+
- API Keys for:
  - Anthropic
  - OpenAI (optional)
  - Sonix
  - Pinecone or Weaviate (optional)

## 🛠️ Installation

### Option 1: Automated Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd knowledge_capture_mvp
```

2. Run the setup script:
```bash
python setup.py
```

3. Edit the `.env` file with your API keys and configuration.

4. Start the application:
```bash
# Start backend
python main.py

# Start frontend (in another terminal)
streamlit run frontend/streamlit_app.py
```

### Option 2: Docker Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd knowledge_capture_mvp
```

2. Copy and edit environment file:
```bash
cp .env.template .env
# Edit .env with your API keys
```

3. Start with Docker Compose:
```bash
docker-compose up -d
```

The application will be available at:
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Option 3: Manual Setup

1. **Setup Python Environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

2. **Setup Databases**:
```bash
# PostgreSQL
createdb knowledge_capture

# Start Redis
redis-server

# Start MongoDB
mongod
```

3. **Configuration**:
```bash
cp .env.template .env
# Edit .env file with your configuration
```

4. **Initialize Database**:
```bash
python -c "from db.connection import create_tables; create_tables()"
```

5. **Start Application**:
```bash
# Backend
uvicorn main:app --reload

# Frontend (in another terminal)
streamlit run frontend/streamlit_app.py
```

## 📖 Usage

### 1. Document Upload
- Navigate to "Document Management"
- Upload job descriptions, SOPs, BMPs, and other organizational documents
- Documents are automatically processed and indexed for search

### 2. Job Roles & Interviews
- Create job roles in the system
- Generate AI-powered interview questions
- Upload interview recordings for automatic transcription

### 3. Knowledge Report Generation
- Generate comprehensive knowledge reports from completed interviews
- Reports include SWOT analysis and structured data for RAG

### 4. Chat Assistant
- Chat with the organizational knowledge base
- Get answers based on all uploaded documents and knowledge reports
- Sources are automatically cited

### 5. Chat with Files
- Upload individual files for targeted Q&A
- Perfect for analyzing specific documents

### 6. System Maintenance
- Automated maintenance tasks keep the system current
- Manual maintenance options for administrators

## 🔧 Configuration

Key configuration options in `.env`:

```env
# API Keys
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
SONIX_API_KEY=your_sonix_api_key

# Database URLs
DATABASE_URL=postgresql://user:password@localhost/knowledge_capture
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-super-secret-key
```

## 🛡️ Security

- JWT-based authentication
- Role-based access control (admin, manager, user)
- Secure file upload with validation
- Audit logging for all actions
- Data encryption at rest and in transit

## 📚 API Documentation

Once the backend is running, visit:
- Interactive API docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## 🧪 Testing

Run tests:
```bash
pytest tests/
```

## 🚀 Deployment

### Production Deployment with Docker

1. **Update docker-compose.prod.yml** for production settings
2. **Configure environment variables** for production
3. **Setup SSL/TLS** with reverse proxy (nginx)
4. **Configure backup strategies** for databases
5. **Setup monitoring** and logging

### Environment Variables for Production

```env
DEBUG=False
SECRET_KEY=production-secret-key
DATABASE_URL=postgresql://prod_user:prod_password@db:5432/knowledge_capture
```

## 📝 Maintenance

The system includes automated maintenance tasks:

- **Daily**: Cleanup old chat sessions, validate transcriptions
- **Weekly**: Review outdated content, backup database  
- **Monthly**: Reindex vector database, audit user access, suggest report updates

Manual maintenance tasks can be run from the admin interface.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation at http://localhost:8000/docs
- Review the troubleshooting section below

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**:
   - Ensure PostgreSQL is running
   - Check DATABASE_URL in .env file
   - Verify database exists

2. **API Key Errors**:
   - Verify API keys in .env file
   - Check API key permissions and quotas

3. **File Upload Issues**:
   - Check file size limits
   - Verify upload directory permissions
   - Ensure supported file types

4. **Transcription Failures**:
   - Verify Sonix API key and quota
   - Check audio file format and quality
   - Review transcription service logs

### Logs and Monitoring

- Application logs: Check console output
- Database logs: Check PostgreSQL logs
- File upload logs: Check uploads directory permissions

## 🔄 Version History

- **v1.0.0**: Initial MVP release
  - Document management
  - Interview processing
  - Knowledge report generation
  - RAG-powered chatbot
  - Maintenance system

## 🗺️ Roadmap

- [ ] Enhanced AI model integration
- [ ] Advanced analytics dashboard
- [ ] Mobile application
- [ ] Enterprise SSO integration
- [ ] Advanced reporting features
- [ ] Multi-language support
"""

with open("knowledge_capture_mvp/README.md", "w") as f:
    f.write(readme_content)

# Create test files
test_content = """import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

from main import app
from db.connection import get_db, Base
from models.database import User
from core.auth import get_password_hash

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    return TestClient(app)

@pytest.fixture
def test_user():
    db = TestingSessionLocal()
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test User",
        role="user",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_register_user(client):
    response = client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com", 
            "password": "newpassword",
            "full_name": "New User"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"

def test_login(client, test_user):
    response = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_protected_route(client, test_user):
    # First login to get token
    login_response = client.post(
        "/api/auth/login", 
        json={"username": "testuser", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]
    
    # Test protected route
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"

def test_document_upload(client, test_user):
    # Login first
    login_response = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]
    
    # Create test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document content.")
        test_file_path = f.name
    
    try:
        with open(test_file_path, 'rb') as test_file:
            response = client.post(
                "/api/documents/upload",
                headers={"Authorization": f"Bearer {token}"},
                files={"file": ("test.txt", test_file, "text/plain")},
                data={"document_type": "test", "document_category": "testing"}
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["filename"] == "test.txt"
        
    finally:
        os.unlink(test_file_path)

def test_create_job_role(client, test_user):
    # Login first  
    login_response = client.post(
        "/api/auth/login",
        json={"username": "testuser", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]
    
    # Create job role
    response = client.post(
        "/api/job-roles",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Role",
            "department": "Testing",
            "description": "A test job role"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Role"
    assert data["department"] == "Testing"

def test_unauthorized_access(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 403  # Should be unauthorized

if __name__ == "__main__":
    pytest.main([__file__])
"""

with open("knowledge_capture_mvp/tests/test_main.py", "w") as f:
    f.write(test_content)

# Create init file for tests
with open("knowledge_capture_mvp/tests/__init__.py", "w") as f:
    f.write("")

# Create pytest configuration
pytest_ini_content = """[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
"""

with open("knowledge_capture_mvp/pytest.ini", "w") as f:
    f.write(pytest_ini_content)

# Create scripts for common tasks
run_script_content = """#!/bin/bash
# Development runner script

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

echo -e "${GREEN}🚀 Knowledge Capture MVP Development Server${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠️  Virtual environment not found. Running setup...${NC}"
    python setup.py
fi

# Activate virtual environment
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env file not found. Please create one from .env.template${NC}"
    exit 1
fi

# Start backend and frontend
echo -e "${GREEN}🔄 Starting backend server...${NC}"
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo -e "${GREEN}🔄 Starting frontend server...${NC}"
streamlit run frontend/streamlit_app.py --server.port 8501 --server.address 0.0.0.0 &
FRONTEND_PID=$!

echo -e "${GREEN}✅ Servers started!${NC}"
echo -e "Backend API: http://localhost:8000"
echo -e "Frontend: http://localhost:8501"
echo -e "API Docs: http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop servers${NC}"

# Function to cleanup on exit
cleanup() {
    echo -e "\\n${YELLOW}🛑 Stopping servers...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT

# Wait for processes
wait
"""

with open("knowledge_capture_mvp/scripts/run_dev.sh", "w") as f:
    f.write(run_script_content)

# Make script executable
import stat
script_path = "knowledge_capture_mvp/scripts/run_dev.sh"
st = os.stat(script_path)
os.chmod(script_path, st.st_mode | stat.S_IEXEC)

print("Additional files created!")
print("- README.md")
print("- tests/test_main.py") 
print("- tests/__init__.py")
print("- pytest.ini")
print("- scripts/run_dev.sh")