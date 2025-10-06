
"""Maintenance service for system upkeep tasks."""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from models.database import (
    Document, KnowledgeReport, Interview, MaintenanceLog, 
    User, JobRole, ChatSession, ChatMessage
)
from db.connection import SessionLocal

logger = logging.getLogger(__name__)


class MaintenanceService:
    """Service for automated system maintenance tasks."""
    
    def __init__(self):
        """Initialize maintenance service."""
        self.maintenance_tasks = {
            "content_review": self.review_outdated_content,
            "cleanup_chat_sessions": self.cleanup_old_chat_sessions,
            "validate_transcriptions": self.validate_transcription_completeness,
            "audit_user_access": self.audit_user_access,
        }

    async def review_outdated_content(self) -> List[Dict[str, Any]]:
        """Review and flag potentially outdated content."""
        
        db = SessionLocal()
        try:
            logger.info("Starting content review")
            
            # Find documents older than 6 months
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            old_documents = db.query(Document).filter(
                Document.created_at < six_months_ago
            ).all()

            # Find knowledge reports older than 1 year
            one_year_ago = datetime.utcnow() - timedelta(days=365)
            old_reports = db.query(KnowledgeReport).filter(
                KnowledgeReport.created_at < one_year_ago
            ).all()

            maintenance_actions = []

            # Flag old documents for review
            for doc in old_documents:
                maintenance_actions.append({
                    "type": "document_review",
                    "item_id": doc.id,
                    "description": f"Document {doc.original_filename} is over 6 months old",
                    "priority": "medium"
                })

            # Flag old reports for review
            for report in old_reports:
                maintenance_actions.append({
                    "type": "report_review",
                    "item_id": report.id,
                    "description": f"Knowledge report '{report.title}' is over 1 year old",
                    "priority": "high"
                })

            # Log maintenance actions
            maintenance_log = MaintenanceLog(
                task_type="content_review",
                task_name="Review Outdated Content",
                status="success",
                details={"items_found": len(maintenance_actions)},
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            db.add(maintenance_log)
            db.commit()

            logger.info(f"Content review completed. Found {len(maintenance_actions)} items")
            return maintenance_actions

        except Exception as e:
            logger.error(f"Error during content review: {e}")
            maintenance_log = MaintenanceLog(
                task_type="content_review",
                task_name="Review Outdated Content",
                status="failed",
                error_message=str(e),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            db.add(maintenance_log)
            db.commit()
            raise
        finally:
            db.close()

    async def cleanup_old_chat_sessions(self) -> int:
        """Clean up old chat sessions."""
        
        db = SessionLocal()
        try:
            logger.info("Starting chat session cleanup")
            
            # Delete sessions older than 90 days with no activity
            ninety_days_ago = datetime.utcnow() - timedelta(days=90)
            old_sessions = db.query(ChatSession).filter(
                ChatSession.updated_at < ninety_days_ago
            ).all()

            count = len(old_sessions)
            for session in old_sessions:
                db.delete(session)

            db.commit()

            # Log maintenance action
            maintenance_log = MaintenanceLog(
                task_type="cleanup",
                task_name="Cleanup Old Chat Sessions",
                status="success",
                details={"sessions_deleted": count},
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            db.add(maintenance_log)
            db.commit()

            logger.info(f"Cleaned up {count} old chat sessions")
            return count

        except Exception as e:
            logger.error(f"Error during chat session cleanup: {e}")
            maintenance_log = MaintenanceLog(
                task_type="cleanup",
                task_name="Cleanup Old Chat Sessions",
                status="failed",
                error_message=str(e),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            db.add(maintenance_log)
            db.commit()
            raise
        finally:
            db.close()

    async def validate_transcription_completeness(self) -> List[Dict[str, Any]]:
        """Validate that all interviews have completed transcriptions."""
        
        db = SessionLocal()
        try:
            logger.info("Starting transcription validation")
            
            # Find interviews with pending or failed transcriptions
            incomplete_interviews = db.query(Interview).filter(
                Interview.transcription_status.in_(["pending", "processing", "failed"])
            ).all()

            issues = []
            for interview in incomplete_interviews:
                issues.append({
                    "interview_id": interview.id,
                    "status": interview.transcription_status,
                    "created_at": interview.created_at.isoformat()
                })

            # Log maintenance action
            maintenance_log = MaintenanceLog(
                task_type="validation",
                task_name="Validate Transcription Completeness",
                status="success",
                details={"incomplete_transcriptions": len(issues)},
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            db.add(maintenance_log)
            db.commit()

            logger.info(f"Found {len(issues)} incomplete transcriptions")
            return issues

        except Exception as e:
            logger.error(f"Error during transcription validation: {e}")
            maintenance_log = MaintenanceLog(
                task_type="validation",
                task_name="Validate Transcription Completeness",
                status="failed",
                error_message=str(e),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            db.add(maintenance_log)
            db.commit()
            raise
        finally:
            db.close()

    async def audit_user_access(self) -> Dict[str, Any]:
        """Audit user access and activity."""
        
        db = SessionLocal()
        try:
            logger.info("Starting user access audit")
            
            # Get user statistics
            total_users = db.query(User).count()
            active_users = db.query(User).filter(User.is_active == True).count()
            inactive_users = total_users - active_users
            
            # Get users by role
            users_by_role = db.query(
                User.role,
                func.count(User.id)
            ).group_by(User.role).all()

            audit_results = {
                "total_users": total_users,
                "active_users": active_users,
                "inactive_users": inactive_users,
                "users_by_role": {role: count for role, count in users_by_role}
            }

            # Log maintenance action
            maintenance_log = MaintenanceLog(
                task_type="audit",
                task_name="Audit User Access",
                status="success",
                details=audit_results,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            db.add(maintenance_log)
            db.commit()

            logger.info(f"User access audit completed: {audit_results}")
            return audit_results

        except Exception as e:
            logger.error(f"Error during user access audit: {e}")
            maintenance_log = MaintenanceLog(
                task_type="audit",
                task_name="Audit User Access",
                status="failed",
                error_message=str(e),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            db.add(maintenance_log)
            db.commit()
            raise
        finally:
            db.close()

    async def run_maintenance_task(self, task_name: str) -> Dict[str, Any]:
        """Run a specific maintenance task."""
        
        if task_name not in self.maintenance_tasks:
            raise ValueError(f"Unknown maintenance task: {task_name}")
        
        logger.info(f"Running maintenance task: {task_name}")
        task_func = self.maintenance_tasks[task_name]
        
        try:
            result = await task_func()
            return {
                "task": task_name,
                "status": "success",
                "result": result
            }
        except Exception as e:
            logger.error(f"Maintenance task {task_name} failed: {e}")
            return {
                "task": task_name,
                "status": "failed",
                "error": str(e)
            }

    async def run_all_maintenance_tasks(self) -> List[Dict[str, Any]]:
        """Run all maintenance tasks."""
        
        logger.info("Running all maintenance tasks")
        results = []
        
        for task_name in self.maintenance_tasks.keys():
            result = await self.run_maintenance_task(task_name)
            results.append(result)
        
        logger.info(f"Completed all maintenance tasks: {len(results)} tasks")
        return results


# Global maintenance service instance
maintenance_service = MaintenanceService()
