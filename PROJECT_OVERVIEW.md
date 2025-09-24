# Knowledge Capture MVP - Complete Codebase

## 📁 Project Structure

```
knowledge_capture_mvp/
├── 📁 api/                         # API route modules
├── 📁 config/                      # Configuration files
│   └── settings.py                 # Application settings
├── 📁 core/                        # Core functionality
│   └── auth.py                     # Authentication utilities
├── 📁 db/                          # Database connections
│   └── connection.py               # Database setup
├── 📁 models/                      # Data models
│   └── database.py                 # SQLAlchemy models
├── 📁 services/                    # Business logic services
│   ├── ai_service.py              # AI/LLM integration
│   ├── document_service.py        # Document processing
│   ├── maintenance_service.py     # System maintenance
│   ├── rag_service.py             # RAG and chatbot
│   └── transcription_service.py   # Audio transcription
├── 📁 frontend/                    # User interface
│   └── streamlit_app.py           # Streamlit web app
├── 📁 tests/                       # Test files
│   ├── __init__.py
│   └── test_main.py               # Main test suite
├── 📁 scripts/                     # Utility scripts
│   └── run_dev.sh                 # Development server
├── 📁 utils/                       # Utility functions
├── main.py                         # FastAPI application
├── requirements.txt                # Python dependencies
├── .env.template                   # Environment variables template
├── setup.py                        # Setup script
├── Dockerfile                      # Backend container
├── Dockerfile.frontend             # Frontend container
├── docker-compose.yml              # Multi-container setup
├── pytest.ini                     # Test configuration
└── README.md                       # Documentation
```

## 🚀 Quick Start Guide

### 1. Prerequisites Installation

**Required Services:**
- PostgreSQL 15+ (for main database)
- Redis 7+ (for caching and sessions)
- MongoDB 7+ (for document storage)
- Python 3.11+

**API Keys Needed:**
- Anthropic API Key (required)
- OpenAI API Key (optional)
- Sonix API Key (required for transcription)
- Pinecone API Key (optional, for vector search)

### 2. Setup Options

#### Option A: Automated Setup (Recommended)
```bash
git clone <repository-url>
cd knowledge_capture_mvp
python setup.py
```

#### Option B: Docker Setup (Production Ready)
```bash
git clone <repository-url>
cd knowledge_capture_mvp
cp .env.template .env
# Edit .env with your API keys
docker-compose up -d
```

#### Option C: Development Setup
```bash
chmod +x scripts/run_dev.sh
./scripts/run_dev.sh
```

### 3. Configuration

Edit the `.env` file with your credentials:

```env
# Required API Keys
ANTHROPIC_API_KEY=your_anthropic_key_here
SONIX_API_KEY=your_sonix_key_here

# Optional API Keys  
OPENAI_API_KEY=your_openai_key_here
PINECONE_API_KEY=your_pinecone_key_here

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost/knowledge_capture
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-super-secret-key-change-this
```

### 4. Access Points

After setup, access the application at:
- **Frontend UI**: http://localhost:8501
- **API Backend**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

## 🔧 Core Components

### Backend Services

1. **Document Service** (`services/document_service.py`)
   - File upload and validation
   - Text extraction from PDF, DOC, TXT
   - Document storage and indexing

2. **AI Service** (`services/ai_service.py`)
   - Anthropic API integration
   - Interview question generation
   - Knowledge report creation

3. **Transcription Service** (`services/transcription_service.py`)
   - Sonix API integration
   - Audio file processing
   - Transcript generation and formatting

4. **RAG Service** (`services/rag_service.py`)
   - Vector embeddings and search
   - Pinecone/Weaviate integration
   - Chatbot functionality
   - File-specific chat

5. **Maintenance Service** (`services/maintenance_service.py`)
   - Automated content review
   - System health monitoring
   - Database maintenance
   - User access auditing

### Database Models

- **User**: Authentication and role management
- **Document**: File storage and metadata
- **JobRole**: Position definitions
- **Interview**: Recording and transcription data
- **KnowledgeReport**: Generated reports with SWOT
- **ChatSession/ChatMessage**: Conversation history
- **MaintenanceLog**: System maintenance tracking

### Frontend Features

- **Document Management**: Upload, organize, and view documents
- **Role & Interview Management**: Create roles, generate questions, process interviews
- **Knowledge Reports**: View and manage generated reports
- **Chat Assistant**: Interactive Q&A with knowledge base
- **Chat with Files**: Upload and query specific documents
- **System Maintenance**: Admin tools for system management

## 🛠️ Development Workflow

### 1. Adding New Features

1. **Database Model** (if needed):
   ```python
   # models/database.py
   class NewModel(Base):
       __tablename__ = "new_models"
       # Add fields
   ```

2. **Service Layer**:
   ```python
   # services/new_service.py
   class NewService:
       async def new_method(self):
           # Business logic
   ```

3. **API Endpoints**:
   ```python
   # main.py or api/new_routes.py
   @app.post("/api/new-endpoint")
   async def new_endpoint():
       # API logic
   ```

4. **Frontend Integration**:
   ```python
   # frontend/streamlit_app.py
   def new_page(self):
       # UI logic
   ```

### 2. Testing

Run tests:
```bash
pytest tests/
```

Add new tests:
```python
# tests/test_new_feature.py
def test_new_feature():
    # Test logic
```

### 3. Database Migrations

For schema changes:
```python
# Update models/database.py
# Run: python -c "from db.connection import create_tables; create_tables()"
```

## 🐛 Troubleshooting

### Common Issues:

1. **Database Connection**:
   - Check if PostgreSQL is running: `sudo systemctl status postgresql`
   - Verify connection string in .env

2. **API Keys**:
   - Verify keys in .env file
   - Check API quotas and permissions

3. **File Uploads**:
   - Check `uploads/` directory permissions
   - Verify file size limits in settings

4. **Transcription**:
   - Ensure Sonix API key is valid
   - Check audio file formats (WAV, MP3, MP4, M4A)

5. **Vector Search**:
   - Verify Pinecone/Weaviate configuration
   - Check embedding model installation

### Logs and Debugging:

- **Application Logs**: Check console output
- **Database Logs**: Check PostgreSQL logs
- **API Debugging**: Use /docs endpoint for testing
- **Frontend Debugging**: Check Streamlit console

## 🚀 Deployment

### Production Deployment:

1. **Environment Configuration**:
   ```bash
   cp .env.template .env.production
   # Configure production values
   ```

2. **Docker Deployment**:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

3. **Security Considerations**:
   - Use strong SECRET_KEY
   - Enable HTTPS/TLS
   - Configure firewall rules
   - Set up backup strategies
   - Enable audit logging

### Scaling:

- **Database**: Use read replicas for PostgreSQL
- **Cache**: Redis clustering for high availability  
- **Storage**: Use cloud storage for file uploads
- **Load Balancing**: Multiple app instances behind load balancer

## 📊 System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Databases     │
│   (Streamlit)   │◄──►│   (FastAPI)     │◄──►│   PostgreSQL    │
│   Port: 8501    │    │   Port: 8000    │    │   MongoDB       │
└─────────────────┘    └─────────────────┘    │   Redis         │
                                              └─────────────────┘
                                                      │
                              ┌─────────────────────────────┐
                              │    External APIs            │
                              │  • Anthropic (AI)          │
                              │  • Sonix (Transcription)   │
                              │  • Pinecone (Vectors)      │
                              └─────────────────────────────┘
```

## 📈 Performance Optimization

1. **Database Indexing**: Proper indexes on frequently queried fields
2. **Caching**: Redis for session and query caching
3. **Vector Search**: Optimized embeddings and chunking
4. **File Processing**: Async processing for large files
5. **Background Tasks**: Celery for heavy computations

## 🔒 Security Features

- JWT-based authentication
- Role-based access control (RBAC)
- File upload validation and sanitization
- SQL injection prevention via SQLAlchemy ORM
- XSS protection in frontend
- API rate limiting
- Audit logging for all actions
- Data encryption at rest and in transit

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Database Schema**: See `models/database.py`
- **Configuration Options**: See `config/settings.py`
- **Test Suite**: See `tests/` directory

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push branch: `git push origin feature/new-feature`
5. Submit Pull Request

## 📄 License

MIT License - see LICENSE file for details.
