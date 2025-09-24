from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import List, Optional, Dict, Any
import uuid
import json
from pathlib import Path

# Internal imports
from config.settings import settings
from db.connection import get_db, create_tables
from core.auth import (
    get_current_user, get_current_active_user, require_admin,
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
    description="Knowledge Capture MVP for Organizational Continuity",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()
    # Schedule maintenance tasks
    await maintenance_service.schedule_maintenance_tasks()

# Pydantic models for request/response
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str
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

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    file_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    session_id: str
    sources: List[Dict[str, Any]]

# Authentication endpoints
@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
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

    return db_user

@app.post("/api/auth/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_data.username).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    return current_user

# Document endpoints
@app.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    document_category: str = Form("general"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        # Process and save document
        document = await document_processor.process_document(
            file, document_type, document_category, current_user, db
        )

        # Index document for RAG
        await rag_service.index_document(document)

        return {
            "id": document.id,
            "filename": document.original_filename,
            "file_type": document.file_type,
            "document_category": document.document_category,
            "status": "processed"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents")
async def list_documents(
    document_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(Document)
    if document_type:
        query = query.filter(Document.file_type == document_type)

    documents = query.all()

    return [
        {
            "id": doc.id,
            "filename": doc.original_filename,
            "file_type": doc.file_type,
            "document_category": doc.document_category,
            "uploaded_at": doc.uploaded_at,
            "file_size": doc.file_size
        }
        for doc in documents
    ]

@app.get("/api/documents/{document_id}")
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "id": document.id,
        "filename": document.original_filename,
        "file_type": document.file_type,
        "document_category": document.document_category,
        "content_text": document.content_text,
        "uploaded_at": document.uploaded_at,
        "uploaded_by": document.uploaded_by.username if document.uploaded_by else None
    }

# Job role endpoints
@app.post("/api/job-roles")
async def create_job_role(
    role_data: JobRoleCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    job_role = JobRole(
        title=role_data.title,
        department=role_data.department,
        description=role_data.description
    )
    db.add(job_role)
    db.commit()
    db.refresh(job_role)

    return {
        "id": job_role.id,
        "title": job_role.title,
        "department": job_role.department,
        "description": job_role.description
    }

@app.get("/api/job-roles")
async def list_job_roles(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    roles = db.query(JobRole).all()
    return [
        {
            "id": role.id,
            "title": role.title,
            "department": role.department,
            "description": role.description
        }
        for role in roles
    ]

# Interview endpoints
@app.post("/api/interviews/generate-questions/{job_role_id}")
async def generate_interview_questions(
    job_role_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    job_role = db.query(JobRole).filter(JobRole.id == job_role_id).first()
    if not job_role:
        raise HTTPException(status_code=404, detail="Job role not found")

    # Get related documents
    related_docs = document_processor.get_documents_for_role(
        db, [job_role.title, job_role.department or ""]
    )

    # Generate questions
    questions = await ai_service.generate_interview_questions(
        job_role.title,
        job_role.description or "",
        related_docs
    )

    return {"questions": questions}

@app.post("/api/interviews/upload-audio/{job_role_id}")
async def upload_interview_audio(
    job_role_id: int,
    audio_file: UploadFile = File(...),
    interviewee_id: int = Form(...),
    interviewer_name: str = Form(...),
    questions: str = Form(...),  # JSON string of questions
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    job_role = db.query(JobRole).filter(JobRole.id == job_role_id).first()
    if not job_role:
        raise HTTPException(status_code=404, detail="Job role not found")

    # Save audio file
    audio_path = await document_processor.save_uploaded_file(audio_file)

    # Create interview record
    interview = Interview(
        job_role_id=job_role_id,
        interviewee_id=interviewee_id,
        interviewer_name=interviewer_name,
        questions=json.loads(questions),
        audio_file_path=audio_path,
        transcription_status="pending"
    )
    db.add(interview)
    db.commit()
    db.refresh(interview)

    # Start transcription in background
    background_tasks.add_task(
        transcription_service.upload_and_transcribe,
        audio_path, interview.id, db
    )

    return {
        "interview_id": interview.id,
        "status": "uploaded",
        "transcription_status": "pending"
    }

@app.get("/api/interviews/{interview_id}/status")
async def get_interview_status(
    interview_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    return {
        "interview_id": interview.id,
        "transcription_status": interview.transcription_status,
        "transcript_available": bool(interview.transcript),
        "duration_minutes": interview.duration_minutes
    }

# Knowledge report endpoints
@app.post("/api/knowledge-reports/generate/{interview_id}")
async def generate_knowledge_report(
    interview_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")

    if not interview.transcript:
        raise HTTPException(status_code=400, detail="Interview transcript not available")

    # Get related documents
    related_docs = document_processor.get_documents_for_role(
        db, [interview.job_role.title, interview.job_role.department or ""]
    )

    # Generate report
    report_data = await ai_service.generate_knowledge_report(
        interview.job_role, interview, related_docs, db
    )

    # Create report record
    knowledge_report = KnowledgeReport(
        job_role_id=interview.job_role_id,
        title=f"{interview.job_role.title} - Knowledge Transfer Report",
        content=report_data["content"],
        swot_analysis=report_data["swot_analysis"],
        structured_data=report_data["structured_data"],
        document_ids=[doc.id for doc in related_docs],
        interview_ids=[interview.id],
        status="draft"
    )

    db.add(knowledge_report)
    db.commit()
    db.refresh(knowledge_report)

    # Index report for RAG
    await rag_service.index_knowledge_report(knowledge_report)

    return {
        "report_id": knowledge_report.id,
        "title": knowledge_report.title,
        "status": knowledge_report.status
    }

@app.get("/api/knowledge-reports")
async def list_knowledge_reports(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    reports = db.query(KnowledgeReport).all()

    return [
        {
            "id": report.id,
            "title": report.title,
            "job_role": report.job_role.title if report.job_role else None,
            "status": report.status,
            "created_at": report.created_at,
            "updated_at": report.updated_at
        }
        for report in reports
    ]

@app.get("/api/knowledge-reports/{report_id}")
async def get_knowledge_report(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    report = db.query(KnowledgeReport).filter(KnowledgeReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Knowledge report not found")

    return {
        "id": report.id,
        "title": report.title,
        "content": report.content,
        "swot_analysis": report.swot_analysis,
        "structured_data": report.structured_data,
        "job_role": report.job_role.title if report.job_role else None,
        "status": report.status,
        "created_at": report.created_at,
        "updated_at": report.updated_at
    }

# Chat endpoints
@app.post("/api/chat/message", response_model=ChatResponse)
async def chat_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    try:
        response, session_id, sources = await rag_service.chat_with_knowledge_base(
            query=chat_request.message,
            user=current_user,
            session_id=chat_request.session_id,
            file_id=chat_request.file_id,
            db=db
        )

        return ChatResponse(
            response=response,
            session_id=session_id,
            sources=sources
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat/upload-file")
async def upload_chat_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user)
):
    # Generate unique file ID
    file_id = str(uuid.uuid4())

    # Extract text from file
    file_path = await document_processor.save_uploaded_file(file)
    content = document_processor.extract_text(file_path)

    # Index content for chat
    await rag_service.index_flat_file_content(file_id, content, file.filename)

    return {
        "file_id": file_id,
        "filename": file.filename,
        "status": "ready_for_chat"
    }

@app.get("/api/chat/history/{session_id}")
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return rag_service.get_chat_history(session_id, db)

# Maintenance endpoints
@app.post("/api/maintenance/run-task/{task_name}")
async def run_maintenance_task(
    task_name: str,
    current_user: User = Depends(require_admin),
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(maintenance_service.run_maintenance_task, task_name)
    return {"message": f"Maintenance task '{task_name}' started in background"}

@app.get("/api/maintenance/history")
async def get_maintenance_history(
    limit: int = 50,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    return maintenance_service.get_maintenance_history(db, limit)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
