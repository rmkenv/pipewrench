"""
Pipewrench - Knowledge Capture and Management System
Main FastAPI application with production-ready error handling and logging.
"""
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.security import HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr
import uuid
import logging

# Internal imports
from config.settings import settings
from config.logging_config import logger
from db.connection import get_db, create_tables
from core.auth import (
    get_current_user, get_current_active_user, require_admin, require_manager,
    create_access_token, verify_password, get_password_hash
)
from models.database import (
    User, Document, JobRole, Interview, KnowledgeReport, 
    ChatSession, ChatMessage, MaintenanceLog
)
from services.document_service import document_processor
from services.ai_service import ai_service
from services.transcription_service import transcription_service
from services.rag_service import rag_service
from services.maintenance_service import maintenance_service

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Pipewrench - Knowledge Capture and Management System for Organizational Continuity",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware with proper configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()


# Pydantic models for request/response
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "user"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class JobRoleCreate(BaseModel):
    title: str
    department: Optional[str] = None
    description: Optional[str] = None


class JobRoleResponse(BaseModel):
    id: int
    title: str
    department: Optional[str]
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: List[Dict[str, Any]]


class MaintenanceTaskRequest(BaseModel):
    task_name: str


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with proper logging."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail} - {request.url}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    try:
        logger.info("Starting Pipewrench application...")
        create_tables()
        logger.info("Database tables created/verified")
        logger.info(f"Application started successfully on {settings.host}:{settings.port}")
    except Exception as e:
        logger.error(f"Startup failed: {e}", exc_info=True)
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    logger.info("Shutting down Pipewrench application...")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post("/api/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    try:
        # Check if user exists
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(status_code=400, detail="Username already registered")

        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=user_data.role
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)

        logger.info(f"New user registered: {user_data.username}")
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error creating user")


@app.post("/api/auth/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login and get access token."""
    try:
        user = db.query(User).filter(User.username == login_data.username).first()

        if not user or not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Inactive user")

        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )

        logger.info(f"User logged in: {user.username}")
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail="Login error")


@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


# ============================================================================
# Document Endpoints
# ============================================================================

@app.post("/api/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Upload and process a document."""
    try:
        # Process and save document
        document = await document_processor.process_document(
            file, document_type, current_user, db
        )

        # Index document for RAG in background
        background_tasks.add_task(rag_service.index_document, document)

        logger.info(f"Document uploaded: {document.id} by user {current_user.username}")
        return {
            "id": document.id,
            "filename": document.original_filename,
            "file_type": document.file_type,
            "document_type": document.document_type,
            "status": "processed"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        raise HTTPException(status_code=500, detail="Error processing document")


@app.get("/api/documents")
async def list_documents(
    document_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all documents with optional filtering."""
    try:
        query = db.query(Document)
        if document_type:
            query = query.filter(Document.document_type == document_type)

        documents = query.offset(skip).limit(limit).all()

        return [
            {
                "id": doc.id,
                "filename": doc.original_filename,
                "file_type": doc.file_type,
                "document_type": doc.document_type,
                "created_at": doc.created_at.isoformat(),
                "file_size": doc.file_size
            }
            for doc in documents
        ]
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving documents")


@app.get("/api/documents/{document_id}")
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get document details."""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return {
            "id": document.id,
            "filename": document.original_filename,
            "file_type": document.file_type,
            "document_type": document.document_type,
            "file_size": document.file_size,
            "content_preview": document.content_text[:500] if document.content_text else None,
            "created_at": document.created_at.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving document")


@app.delete("/api/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """Delete a document (manager/admin only)."""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        db.delete(document)
        db.commit()
        logger.info(f"Document deleted: {document_id} by user {current_user.username}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting document")


# ============================================================================
# Job Role Endpoints
# ============================================================================

@app.post("/api/job-roles", response_model=JobRoleResponse, status_code=status.HTTP_201_CREATED)
async def create_job_role(
    role_data: JobRoleCreate,
    current_user: User = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """Create a new job role (manager/admin only)."""
    try:
        job_role = JobRole(
            title=role_data.title,
            department=role_data.department,
            description=role_data.description
        )
        db.add(job_role)
        db.commit()
        db.refresh(job_role)

        logger.info(f"Job role created: {job_role.id} by user {current_user.username}")
        return job_role
    except Exception as e:
        logger.error(f"Error creating job role: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error creating job role")


@app.get("/api/job-roles", response_model=List[JobRoleResponse])
async def list_job_roles(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all job roles."""
    try:
        job_roles = db.query(JobRole).offset(skip).limit(limit).all()
        return job_roles
    except Exception as e:
        logger.error(f"Error listing job roles: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving job roles")


@app.get("/api/job-roles/{role_id}", response_model=JobRoleResponse)
async def get_job_role(
    role_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get job role details."""
    try:
        job_role = db.query(JobRole).filter(JobRole.id == role_id).first()
        if not job_role:
            raise HTTPException(status_code=404, detail="Job role not found")
        return job_role
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job role: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving job role")


@app.post("/api/job-roles/{role_id}/generate-questions")
async def generate_interview_questions(
    role_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Generate interview questions for a job role."""
    try:
        job_role = db.query(JobRole).filter(JobRole.id == role_id).first()
        if not job_role:
            raise HTTPException(status_code=404, detail="Job role not found")

        # Get related documents
        related_documents = db.query(Document).limit(10).all()

        # Generate questions
        questions = await ai_service.generate_interview_questions(
            job_role.title,
            job_role.description or "",
            related_documents
        )

        logger.info(f"Generated {len(questions)} questions for role {role_id}")
        return {"questions": questions}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating questions: {e}")
        raise HTTPException(status_code=500, detail="Error generating questions")


# ============================================================================
# Interview Endpoints
# ============================================================================

@app.post("/api/interviews", status_code=status.HTTP_201_CREATED)
async def create_interview(
    job_role_id: int = Form(...),
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Create a new interview with audio file."""
    try:
        # Validate job role exists
        job_role = db.query(JobRole).filter(JobRole.id == job_role_id).first()
        if not job_role:
            raise HTTPException(status_code=404, detail="Job role not found")

        # Save audio file
        audio_path = await document_processor.save_uploaded_file(audio_file)

        # Create interview record
        interview = Interview(
            job_role_id=job_role_id,
            interviewee_id=current_user.id,
            audio_file_path=audio_path,
            transcription_status="pending"
        )
        db.add(interview)
        db.commit()
        db.refresh(interview)

        # Start transcription in background
        if transcription_service.enabled:
            background_tasks.add_task(
                transcription_service.upload_and_transcribe,
                audio_path,
                interview.id,
                db
            )

        logger.info(f"Interview created: {interview.id}")
        return {
            "id": interview.id,
            "job_role_id": job_role_id,
            "status": "created",
            "transcription_status": interview.transcription_status
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating interview: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error creating interview")


@app.get("/api/interviews")
async def list_interviews(
    job_role_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all interviews."""
    try:
        query = db.query(Interview)
        if job_role_id:
            query = query.filter(Interview.job_role_id == job_role_id)

        interviews = query.offset(skip).limit(limit).all()

        return [
            {
                "id": interview.id,
                "job_role_id": interview.job_role_id,
                "interviewee_id": interview.interviewee_id,
                "transcription_status": interview.transcription_status,
                "created_at": interview.created_at.isoformat()
            }
            for interview in interviews
        ]
    except Exception as e:
        logger.error(f"Error listing interviews: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving interviews")


# ============================================================================
# Chat/RAG Endpoints
# ============================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Chat with the knowledge base using RAG."""
    try:
        response_text, session_id, sources = await rag_service.chat(
            chat_request.message,
            chat_request.session_id,
            current_user,
            db
        )

        return ChatResponse(
            response=response_text,
            session_id=session_id,
            sources=sources
        )
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail="Error processing chat request")


@app.get("/api/chat/sessions")
async def list_chat_sessions(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List user's chat sessions."""
    try:
        sessions = db.query(ChatSession).filter(
            ChatSession.user_id == current_user.id
        ).order_by(ChatSession.updated_at.desc()).offset(skip).limit(limit).all()

        return [
            {
                "session_id": session.session_id,
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat()
            }
            for session in sessions
        ]
    except Exception as e:
        logger.error(f"Error listing chat sessions: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving chat sessions")


# ============================================================================
# Maintenance Endpoints
# ============================================================================

@app.post("/api/maintenance/run-task")
async def run_maintenance_task(
    task_request: MaintenanceTaskRequest,
    current_user: User = Depends(require_admin),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Run a specific maintenance task (admin only)."""
    try:
        background_tasks.add_task(
            maintenance_service.run_maintenance_task,
            task_request.task_name
        )
        
        logger.info(f"Maintenance task started: {task_request.task_name} by {current_user.username}")
        return {
            "status": "started",
            "task": task_request.task_name,
            "message": "Maintenance task started in background"
        }
    except Exception as e:
        logger.error(f"Error starting maintenance task: {e}")
        raise HTTPException(status_code=500, detail="Error starting maintenance task")


@app.get("/api/maintenance/logs")
async def get_maintenance_logs(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get maintenance logs (admin only)."""
    try:
        logs = db.query(MaintenanceLog).order_by(
            MaintenanceLog.created_at.desc()
        ).offset(skip).limit(limit).all()

        return [
            {
                "id": log.id,
                "task_type": log.task_type,
                "task_name": log.task_name,
                "status": log.status,
                "details": log.details,
                "error_message": log.error_message,
                "created_at": log.created_at.isoformat()
            }
            for log in logs
        ]
    except Exception as e:
        logger.error(f"Error getting maintenance logs: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving maintenance logs")


# ============================================================================
# Admin Endpoints
# ============================================================================

@app.get("/api/admin/users")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    try:
        users = db.query(User).offset(skip).limit(limit).all()
        return [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat()
            }
            for user in users
        ]
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving users")


@app.patch("/api/admin/users/{user_id}")
async def update_user(
    user_id: int,
    is_active: Optional[bool] = None,
    role: Optional[str] = None,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update user (admin only)."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if is_active is not None:
            user.is_active = is_active
        if role is not None:
            if role not in ["admin", "manager", "user"]:
                raise HTTPException(status_code=400, detail="Invalid role")
            user.role = role

        db.commit()
        db.refresh(user)

        logger.info(f"User updated: {user_id} by admin {current_user.username}")
        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "is_active": user.is_active
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error updating user")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
