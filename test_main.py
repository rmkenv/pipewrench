
"""
Test suite for Pipewrench application.
Run with: pytest test_main.py -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from models.database import Base
from db.connection import get_db

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class TestHealthAndRoot:
    """Test health check and root endpoints."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
    
    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data


class TestAuthentication:
    """Test authentication endpoints."""
    
    def test_register_user(self):
        """Test user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "testpassword123",
                "full_name": "Test User"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "id" in data
    
    def test_register_duplicate_username(self):
        """Test registration with duplicate username."""
        # First registration
        client.post(
            "/api/auth/register",
            json={
                "username": "duplicate",
                "email": "unique@example.com",
                "password": "testpassword123"
            }
        )
        
        # Duplicate registration
        response = client.post(
            "/api/auth/register",
            json={
                "username": "duplicate",
                "email": "another@example.com",
                "password": "testpassword123"
            }
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_login_success(self):
        """Test successful login."""
        # Register user first
        client.post(
            "/api/auth/register",
            json={
                "username": "logintest",
                "email": "login@example.com",
                "password": "testpassword123"
            }
        )
        
        # Login
        response = client.post(
            "/api/auth/login",
            json={
                "username": "logintest",
                "password": "testpassword123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_wrong_password(self):
        """Test login with wrong password."""
        # Register user first
        client.post(
            "/api/auth/register",
            json={
                "username": "wrongpass",
                "email": "wrongpass@example.com",
                "password": "correctpassword123"
            }
        )
        
        # Login with wrong password
        response = client.post(
            "/api/auth/login",
            json={
                "username": "wrongpass",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
    
    def test_get_current_user(self):
        """Test getting current user info."""
        # Register and login
        client.post(
            "/api/auth/register",
            json={
                "username": "currentuser",
                "email": "current@example.com",
                "password": "testpassword123"
            }
        )
        
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "currentuser",
                "password": "testpassword123"
            }
        )
        token = login_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "currentuser"


class TestJobRoles:
    """Test job role endpoints."""
    
    @pytest.fixture
    def auth_headers(self):
        """Create authenticated user and return headers."""
        # Register admin user
        client.post(
            "/api/auth/register",
            json={
                "username": "admin",
                "email": "admin@example.com",
                "password": "adminpass123",
                "role": "admin"
            }
        )
        
        # Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "admin",
                "password": "adminpass123"
            }
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_create_job_role(self, auth_headers):
        """Test creating a job role."""
        response = client.post(
            "/api/job-roles",
            json={
                "title": "Software Engineer",
                "department": "Engineering",
                "description": "Develops software applications"
            },
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Software Engineer"
        assert data["department"] == "Engineering"
    
    def test_list_job_roles(self, auth_headers):
        """Test listing job roles."""
        # Create a job role first
        client.post(
            "/api/job-roles",
            json={
                "title": "Data Analyst",
                "department": "Analytics"
            },
            headers=auth_headers
        )
        
        # List job roles
        response = client.get("/api/job-roles", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0


class TestDocuments:
    """Test document endpoints."""
    
    @pytest.fixture
    def auth_headers(self):
        """Create authenticated user and return headers."""
        client.post(
            "/api/auth/register",
            json={
                "username": "docuser",
                "email": "doc@example.com",
                "password": "docpass123"
            }
        )
        
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "docuser",
                "password": "docpass123"
            }
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_list_documents_empty(self, auth_headers):
        """Test listing documents when none exist."""
        response = client.get("/api/documents", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestChat:
    """Test chat/RAG endpoints."""
    
    @pytest.fixture
    def auth_headers(self):
        """Create authenticated user and return headers."""
        client.post(
            "/api/auth/register",
            json={
                "username": "chatuser",
                "email": "chat@example.com",
                "password": "chatpass123"
            }
        )
        
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": "chatuser",
                "password": "chatpass123"
            }
        )
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_list_chat_sessions_empty(self, auth_headers):
        """Test listing chat sessions when none exist."""
        response = client.get("/api/chat/sessions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
