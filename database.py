from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="user")  # admin, manager, user
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    documents = relationship("Document", back_populates="uploaded_by")
    interviews = relationship("Interview", back_populates="interviewee")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # job_description, sop, bmp, etc.
    document_category = Column(String)  # industry_standard, permit_requirement, etc.
    file_size = Column(Integer)
    mime_type = Column(String)
    content_text = Column(Text)  # Extracted text content
    metadata = Column(JSON)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=func.now())
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime)

    # Relationships
    uploaded_by = relationship("User", back_populates="documents")

class JobRole(Base):
    __tablename__ = "job_roles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    department = Column(String)
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())

    # Relationships
    interviews = relationship("Interview", back_populates="job_role")
    reports = relationship("KnowledgeReport", back_populates="job_role")

class Interview(Base):
    __tablename__ = "interviews"

    id = Column(Integer, primary_key=True, index=True)
    job_role_id = Column(Integer, ForeignKey("job_roles.id"))
    interviewee_id = Column(Integer, ForeignKey("users.id"))
    interviewer_name = Column(String)
    questions = Column(JSON)  # Generated questions
    audio_file_path = Column(String)
    transcript = Column(Text)
    duration_minutes = Column(Integer)
    interview_date = Column(DateTime, default=func.now())
    transcription_status = Column(String, default="pending")  # pending, processing, completed, failed
    transcription_job_id = Column(String)  # Sonix job ID

    # Relationships
    job_role = relationship("JobRole", back_populates="interviews")
    interviewee = relationship("User", back_populates="interviews")

class KnowledgeReport(Base):
    __tablename__ = "knowledge_reports"

    id = Column(Integer, primary_key=True, index=True)
    job_role_id = Column(Integer, ForeignKey("job_roles.id"))
    title = Column(String, nullable=False)
    content = Column(Text)  # Generated report content
    swot_analysis = Column(JSON)  # Structured SWOT data
    structured_data = Column(JSON)  # RAG-ready structured data
    document_ids = Column(JSON)  # List of document IDs used
    interview_ids = Column(JSON)  # List of interview IDs used
    version = Column(Integer, default=1)
    status = Column(String, default="draft")  # draft, review, approved, archived
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    job_role = relationship("JobRole", back_populates="reports")

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime, default=func.now())
    last_activity = Column(DateTime, default=func.now())

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("chat_sessions.session_id"))
    message_type = Column(String)  # user, assistant, system
    content = Column(Text)
    sources = Column(JSON)  # Referenced documents/reports
    timestamp = Column(DateTime, default=func.now())

class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"

    id = Column(Integer, primary_key=True, index=True)
    action_type = Column(String)  # update, review, archive, backup
    description = Column(Text)
    affected_items = Column(JSON)  # IDs of affected documents/reports
    performed_by_id = Column(Integer, ForeignKey("users.id"))
    performed_at = Column(DateTime, default=func.now())
    status = Column(String)  # completed, failed, in_progress
