# Knowledge Capture MVP

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
git clone <https://github.com/rmkenv/pipewrench>
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
source venv/bin/activate  # On Windows: venv\Scripts\activate
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
