import pytest
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
