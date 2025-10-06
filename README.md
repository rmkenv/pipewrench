# Pipewrench - Knowledge Capture and Management System

A comprehensive, production-ready system for capturing, preserving, and operationalizing organizational knowledge through AI-powered document ingestion, employee interviews, and chatbot training.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Features

- **Document Management**: Upload and process various document types (PDF, DOC, DOCX, TXT)
- **AI-Powered Question Generation**: Generate tailored interview questions using Anthropic Claude or OpenAI GPT
- **Audio Transcription**: Automatic transcription using Sonix API
- **Knowledge Report Generation**: AI-generated comprehensive reports for each role
- **RAG-Powered Chatbot**: Chat with organizational knowledge base using vector search
- **Ongoing Maintenance**: Automated system maintenance and content review
- **Security**: Role-based access control, JWT authentication, and audit trails
- **Production-Ready**: Comprehensive error handling, logging, and monitoring

## 🏗️ Architecture

- **Backend**: FastAPI with Python 3.11+
- **Frontend**: Streamlit web interface
- **Database**: PostgreSQL (main data), MongoDB (documents - optional), Redis (caching - optional)
- **Vector Database**: Pinecone or in-memory (for RAG)
- **AI Services**: Anthropic Claude, OpenAI GPT, Sonix transcription
- **Authentication**: JWT-based with role-based access control

## 📋 Prerequisites

- Python 3.11 or higher
- PostgreSQL 15+ (required)
- Redis 7+ (optional, for caching)
- MongoDB 7+ (optional, for document storage)
- API Keys for:
  - Anthropic Claude (recommended) or OpenAI GPT
  - Sonix (for transcription - optional)
  - Pinecone (for vector database - optional)

## 🛠️ Installation

### Quick Start (Recommended)

1. **Clone the repository**:
```bash
git clone https://github.com/rmkenv/pipewrench.git
cd pipewrench
```

2. **Run the setup script**:
```bash
chmod +x run_dev.sh
./run_dev.sh
```

3. **Configure environment variables**:
```bash
cp .env.template .env
# Edit .env with your API keys and configuration
nano .env
```

4. **Start the application**:
```bash
python main.py
```

The application will be available at:
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### Manual Installation

1. **Create and activate virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

3. **Setup PostgreSQL database**:
```bash
# Create database
createdb pipewrench

# Or using psql
psql -U postgres
CREATE DATABASE pipewrench;
\q
```

4. **Configure environment**:
```bash
cp .env.template .env
# Edit .env file with your configuration
```

5. **Initialize database**:
```bash
python -c "from db.connection import create_tables; create_tables()"
```

6. **Start the application**:
```bash
python main.py
```

### Docker Installation

1. **Build and start containers**:
```bash
docker-compose up -d
```

2. **Configure environment**:
```bash
cp .env.template .env
# Edit .env with your configuration
```

The application will be available at:
- Frontend: http://localhost:8501
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## ⚙️ Configuration

### Required Environment Variables

```env
# API Keys (at least one AI provider required)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Database (PostgreSQL required)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pipewrench

# Security (change in production!)
SECRET_KEY=your-super-secret-key-change-this-in-production
```

### Optional Environment Variables

```env
# Transcription Service
SONIX_API_KEY=your_sonix_api_key_here

# Vector Database
PINECONE_API_KEY=your_pinecone_api_key_here

# Optional Databases
MONGODB_URL=mongodb://localhost:27017
REDIS_URL=redis://localhost:6379

# Application Settings
DEBUG=False
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8501
```

See `.env.template` for all available configuration options.

## 📖 Usage

### 1. User Registration and Authentication

```bash
# Register a new user
curl -X POST "http://localhost:8000/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "securepassword123",
    "role": "admin"
  }'

# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "securepassword123"
  }'
```

### 2. Document Upload

```bash
# Upload a document
curl -X POST "http://localhost:8000/api/documents/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@document.pdf" \
  -F "document_type=sop"
```

### 3. Job Roles and Interviews

```bash
# Create a job role
curl -X POST "http://localhost:8000/api/job-roles" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Software Engineer",
    "department": "Engineering",
    "description": "Develops software applications"
  }'

# Generate interview questions
curl -X POST "http://localhost:8000/api/job-roles/1/generate-questions" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. Chat with Knowledge Base

```bash
# Send a chat message
curl -X POST "http://localhost:8000/api/chat" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the key responsibilities of a Software Engineer?"
  }'
```

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest test_main.py -v

# Run with coverage
pytest test_main.py -v --cov=. --cov-report=html

# Run specific test class
pytest test_main.py::TestAuthentication -v
```

## 🔧 Development

### Code Quality

```bash
# Format code
black . --exclude venv

# Lint code
flake8 . --exclude=venv --max-line-length=120

# Type checking
mypy . --exclude venv --ignore-missing-imports
```

### Using Makefile

```bash
make help          # Show available commands
make install       # Install dependencies
make dev           # Run development server
make test          # Run tests
make lint          # Run linters
make format        # Format code
make clean         # Clean temporary files
```

## 🚀 Production Deployment

### Security Checklist

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_ORIGINS` with your actual domains
- [ ] Use HTTPS/TLS for all connections
- [ ] Set up proper database backups
- [ ] Configure firewall rules
- [ ] Use environment-specific configuration
- [ ] Enable rate limiting
- [ ] Set up monitoring and alerting
- [ ] Review and update CORS settings

### Deployment Options

#### 1. Traditional Server Deployment

```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

#### 2. Docker Deployment

```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose logs -f

# Scale workers
docker-compose up -d --scale backend=4
```

#### 3. Cloud Deployment

See `docs/deployment/` for platform-specific guides:
- AWS (EC2, ECS, Lambda)
- Google Cloud Platform
- Azure
- Heroku
- DigitalOcean

## 📊 Monitoring and Logging

### Logs

Application logs are stored in `logs/app.log` in JSON format for easy parsing.

```bash
# View logs
tail -f logs/app.log

# Parse JSON logs
cat logs/app.log | jq '.'
```

### Health Check

```bash
# Check application health
curl http://localhost:8000/health
```

### Metrics

The application exposes metrics at `/metrics` (when configured).

## 🛡️ Security

- **Authentication**: JWT-based authentication with configurable expiration
- **Authorization**: Role-based access control (admin, manager, user)
- **Password Security**: Bcrypt hashing with salt
- **Input Validation**: Pydantic models for all inputs
- **CORS**: Configurable allowed origins
- **Rate Limiting**: Recommended for production (use nginx or API gateway)
- **Audit Logging**: All admin actions are logged

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add tests for new features
- Update documentation
- Use type hints
- Add docstrings to functions and classes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support and Troubleshooting

### Common Issues

**1. Database Connection Error**
```bash
# Check PostgreSQL is running
pg_isready

# Verify DATABASE_URL in .env
echo $DATABASE_URL
```

**2. API Key Errors**
```bash
# Verify API keys are set
python -c "from config.settings import settings; print(settings.anthropic_api_key[:10])"
```

**3. Import Errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**4. Port Already in Use**
```bash
# Change port in .env
PORT=8001

# Or kill process using port 8000
lsof -ti:8000 | xargs kill -9
```

### Getting Help

- 📖 [Documentation](http://localhost:8000/docs)
- 🐛 [Issue Tracker](https://github.com/rmkenv/pipewrench/issues)
- 💬 [Discussions](https://github.com/rmkenv/pipewrench/discussions)

## 🗺️ Roadmap

- [ ] Enhanced AI model integration (Claude 3.5, GPT-4)
- [ ] Advanced analytics dashboard
- [ ] Mobile application
- [ ] Enterprise SSO integration
- [ ] Advanced reporting features
- [ ] Multi-language support
- [ ] Real-time collaboration features
- [ ] Advanced search capabilities
- [ ] Integration with popular tools (Slack, Teams, etc.)

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

## 👥 Authors

- **rmkenv** - *Initial work* - [GitHub](https://github.com/rmkenv)

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Anthropic and OpenAI for AI capabilities
- The open-source community for various libraries and tools

---

**Note**: This is a production-ready release with comprehensive error handling, logging, and security features. Always review and test thoroughly before deploying to production.
