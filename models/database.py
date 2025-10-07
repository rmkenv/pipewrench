
"""Database models for the application."""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

Base = declarative_base()


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(20), default="user", nullable=False)  # admin, manager, user
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    documents = relationship("Document", back_populates="uploaded_by_user")
    interviews = relationship("Interview", back_populates="interviewee_user")
    chat_sessions = relationship("ChatSession", back_populates="user")


class Document(Base):
    """Document model for uploaded files."""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_text = Column(Text)
    document_type = Column(String(50))  # job_description, sop, bmp, etc.
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    mongo_id = Column(String(50))  # Reference to MongoDB document
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    uploaded_by_user = relationship("User", back_populates="documents")
    job_roles = relationship("JobRole", secondary="job_role_documents", back_populates="documents")


class JobRole(Base):
    """Job role model."""
    __tablename__ = "job_roles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    department = Column(String(255))
    description = Column(Text)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    documents = relationship("Document", secondary="job_role_documents", back_populates="job_roles")
    interviews = relationship("Interview", back_populates="job_role")
    knowledge_reports = relationship("KnowledgeReport", back_populates="job_role")


class JobRoleDocument(Base):
    """Association table for job roles and documents."""
    __tablename__ = "job_role_documents"

    job_role_id = Column(Integer, ForeignKey("job_roles.id"), primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"), primary_key=True)


class Interview(Base):
    """Interview model for recorded interviews."""
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    job_role_id = Column(Integer, ForeignKey("job_roles.id"), nullable=False)
    interviewee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    audio_file_path = Column(String(500))
    transcription_text = Column(Text)
    transcription_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    questions = Column(JSON)
    answers = Column(JSON)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    job_role = relationship("JobRole", back_populates="interviews")
    interviewee_user = relationship("User", back_populates="interviews")


class KnowledgeReport(Base):
    """Knowledge report model for generated reports."""
    __tablename__ = "knowledge_reports"

    id = Column(Integer, primary_key=True, index=True)
    job_role_id = Column(Integer, ForeignKey("job_roles.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    swot_analysis = Column(JSON)
    key_insights = Column(JSON)
    version = Column(Integer, default=1)
    status = Column(String(50), default="draft")  # draft, published, archived
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    job_role = relationship("JobRole", back_populates="knowledge_reports")


class ChatSession(Base):
    """Chat session model for RAG conversations."""
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255))
    context_type = Column(String(50), default="general")  # general, document, role
    context_id = Column(Integer)  # Reference to document or role
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    """Chat message model."""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    sources = Column(JSON)  # Source documents/references
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")


class MaintenanceLog(Base):
    """Maintenance log model for system maintenance tasks."""
    __tablename__ = "maintenance_logs"

    id = Column(Integer, primary_key=True, index=True)
    task_type = Column(String(100), nullable=False)
    task_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)  # success, failed, in_progress
    details = Column(JSON)
    error_message = Column(Text)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now(), nullable=False)
