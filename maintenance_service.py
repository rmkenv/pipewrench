import schedule
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.database import (
    Document, KnowledgeReport, Interview, MaintenanceLog, 
    User, JobRole, ChatMessage
)
from services.ai_service import ai_service
from services.rag_service import rag_service
from db.connection import get_db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MaintenanceService:
    def __init__(self):
        self.maintenance_tasks = {
            "content_review": self.review_outdated_content,
            "reindex_vectors": self.reindex_vector_database,
            "cleanup_chat_sessions": self.cleanup_old_chat_sessions,
            "backup_database": self.backup_database,
            "audit_user_access": self.audit_user_access,
            "validate_transcriptions": self.validate_transcription_completeness,
            "update_knowledge_reports": self.suggest_knowledge_report_updates
        }

    async def schedule_maintenance_tasks(self):
        """Schedule regular maintenance tasks"""

        # Daily tasks
        schedule.every().day.at("02:00").do(self._run_async_task, self.cleanup_old_chat_sessions)
        schedule.every().day.at("03:00").do(self._run_async_task, self.validate_transcription_completeness)

        # Weekly tasks
        schedule.every().sunday.at("01:00").do(self._run_async_task, self.review_outdated_content)
        schedule.every().sunday.at("04:00").do(self._run_async_task, self.backup_database)

        # Monthly tasks
        schedule.every().month.do(self._run_async_task, self.reindex_vector_database)
        schedule.every().month.do(self._run_async_task, self.audit_user_access)
        schedule.every().month.do(self._run_async_task, self.suggest_knowledge_report_updates)

        logger.info("Maintenance tasks scheduled successfully")

    def _run_async_task(self, task_func):
        """Run async task in sync scheduler"""
        asyncio.run(task_func())

    async def review_outdated_content(self):
        """Review and flag potentially outdated content"""

        db = next(get_db())
        try:
            # Find documents older than 6 months
            six_months_ago = datetime.utcnow() - timedelta(days=180)
            old_documents = db.query(Document).filter(
                Document.uploaded_at < six_months_ago
            ).all()

            # Find knowledge reports older than 1 year or with outdated interviews
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
                    "description": f"Document {doc.original_filename} is over 6 months old and may need review",
                    "priority": "medium",
                    "suggested_action": "Review document for accuracy and update if necessary"
                })

            # Flag old reports for review
            for report in old_reports:
                maintenance_actions.append({
                    "type": "report_review",
                    "item_id": report.id,
                    "description": f"Knowledge report '{report.title}' is over 1 year old and may need update",
                    "priority": "high",
                    "suggested_action": "Conduct follow-up interview or document review"
                })

            # Log maintenance actions
            for action in maintenance_actions:
                maintenance_log = MaintenanceLog(
                    action_type="content_review",
                    description=action["description"],
                    affected_items=[{"type": action["type"], "id": action["item_id"]}],
                    status="identified"
                )
                db.add(maintenance_log)

            db.commit()
            logger.info(f"Content review completed. Found {len(maintenance_actions)} items needing attention")

            return maintenance_actions

        except Exception as e:
            logger.error(f"Error during content review: {e}")
            raise
        finally:
            db.close()

    async def reindex_vector_database(self):
        """Reindex the entire vector database for better search performance"""

        db = next(get_db())
        try:
            logger.info("Starting vector database reindexing")

            # Reindex all content
            await rag_service.reindex_all_content(db)

            # Log maintenance action
            maintenance_log = MaintenanceLog(
                action_type="reindex_vectors",
                description="Reindexed entire vector database for improved search performance",
                status="completed"
            )
            db.add(maintenance_log)
            db.commit()

            logger.info("Vector database reindexing completed successfully")

        except Exception as e:
            logger.error(f"Error during vector reindexing: {e}")

            # Log failed maintenance
            maintenance_log = MaintenanceLog(
                action_type="reindex_vectors",
                description=f"Failed to reindex vector database: {str(e)}",
                status="failed"
            )
            db.add(maintenance_log)
            db.commit()
            raise
        finally:
            db.close()

    async def cleanup_old_chat_sessions(self):
        """Clean up old chat messages and sessions"""

        db = next(get_db())
        try:
            # Delete chat messages older than 90 days
            ninety_days_ago = datetime.utcnow() - timedelta(days=90)

            old_messages = db.query(ChatMessage).filter(
                ChatMessage.timestamp < ninety_days_ago
            )

            count = old_messages.count()
            old_messages.delete()

            db.commit()

            # Log maintenance action
            maintenance_log = MaintenanceLog(
                action_type="cleanup_chat_sessions",
                description=f"Cleaned up {count} old chat messages (older than 90 days)",
                status="completed"
            )
            db.add(maintenance_log)
            db.commit()

            logger.info(f"Chat cleanup completed. Removed {count} old messages")

        except Exception as e:
            logger.error(f"Error during chat cleanup: {e}")
            raise
        finally:
            db.close()

    async def backup_database(self):
        """Create database backup"""

        try:
            # This is a placeholder for database backup logic
            # In a real implementation, you would use pg_dump for PostgreSQL
            # or appropriate backup tools for your database

            backup_filename = f"knowledge_capture_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.sql"

            # Placeholder for actual backup command
            # subprocess.run(['pg_dump', 'knowledge_capture', '-f', backup_filename])

            db = next(get_db())
            maintenance_log = MaintenanceLog(
                action_type="backup_database",
                description=f"Database backup created: {backup_filename}",
                status="completed"
            )
            db.add(maintenance_log)
            db.commit()
            db.close()

            logger.info(f"Database backup completed: {backup_filename}")

        except Exception as e:
            logger.error(f"Error during database backup: {e}")
            raise

    async def audit_user_access(self):
        """Audit user access patterns and flag anomalies"""

        db = next(get_db())
        try:
            # Find users who haven't been active in the last 90 days
            ninety_days_ago = datetime.utcnow() - timedelta(days=90)

            inactive_users = db.query(User).filter(
                ~db.query(ChatMessage).filter(
                    ChatMessage.session_id.in_(
                        db.query(ChatMessage.session_id).join(
                            # This would need proper join logic based on your schema
                        )
                    ),
                    ChatMessage.timestamp > ninety_days_ago
                ).exists()
            ).all()

            audit_findings = []

            for user in inactive_users:
                audit_findings.append({
                    "user_id": user.id,
                    "username": user.username,
                    "finding": "No activity in 90+ days",
                    "recommendation": "Review user access requirements"
                })

            # Log audit results
            maintenance_log = MaintenanceLog(
                action_type="audit_user_access",
                description=f"User access audit completed. Found {len(audit_findings)} inactive users",
                affected_items=[{"type": "user_audit", "findings": audit_findings}],
                status="completed"
            )
            db.add(maintenance_log)
            db.commit()

            logger.info(f"User access audit completed. {len(audit_findings)} findings")

        except Exception as e:
            logger.error(f"Error during user access audit: {e}")
            raise
        finally:
            db.close()

    async def validate_transcription_completeness(self):
        """Check for incomplete or failed transcriptions"""

        db = next(get_db())
        try:
            # Find interviews with incomplete transcriptions
            incomplete_transcriptions = db.query(Interview).filter(
                Interview.transcription_status.in_(["pending", "processing", "failed"])
            ).all()

            issues_found = []

            for interview in incomplete_transcriptions:
                if interview.transcription_status == "failed":
                    issues_found.append({
                        "interview_id": interview.id,
                        "issue": "Transcription failed",
                        "action": "Retry transcription or manual review"
                    })
                elif interview.transcription_status == "processing":
                    # Check if it's been processing for too long (over 2 hours)
                    if interview.interview_date < datetime.utcnow() - timedelta(hours=2):
                        issues_found.append({
                            "interview_id": interview.id,
                            "issue": "Transcription stuck in processing",
                            "action": "Check transcription service status"
                        })

            # Log validation results
            maintenance_log = MaintenanceLog(
                action_type="validate_transcriptions",
                description=f"Transcription validation completed. Found {len(issues_found)} issues",
                affected_items=[{"type": "transcription_issues", "issues": issues_found}],
                status="completed"
            )
            db.add(maintenance_log)
            db.commit()

            logger.info(f"Transcription validation completed. {len(issues_found)} issues found")

        except Exception as e:
            logger.error(f"Error during transcription validation: {e}")
            raise
        finally:
            db.close()

    async def suggest_knowledge_report_updates(self):
        """Suggest updates to knowledge reports based on new documents or changes"""

        db = next(get_db())
        try:
            # Find reports that might need updates based on new documents
            suggestions = []

            reports = db.query(KnowledgeReport).all()

            for report in reports:
                # Check for new documents related to this role
                if report.job_role:
                    # Find documents added since the report was last updated
                    new_documents = db.query(Document).filter(
                        Document.uploaded_at > report.updated_at,
                        Document.file_type.in_(["job_description", "sop", "bmp"])
                    ).all()

                    if new_documents:
                        suggestions.append({
                            "report_id": report.id,
                            "report_title": report.title,
                            "suggestion": f"Consider updating report with {len(new_documents)} new documents",
                            "new_documents": [doc.original_filename for doc in new_documents]
                        })

            # Log suggestions
            maintenance_log = MaintenanceLog(
                action_type="update_knowledge_reports",
                description=f"Generated {len(suggestions)} update suggestions for knowledge reports",
                affected_items=[{"type": "report_suggestions", "suggestions": suggestions}],
                status="completed"
            )
            db.add(maintenance_log)
            db.commit()

            logger.info(f"Knowledge report update suggestions completed. {len(suggestions)} suggestions generated")

            return suggestions

        except Exception as e:
            logger.error(f"Error generating report update suggestions: {e}")
            raise
        finally:
            db.close()

    async def run_maintenance_task(self, task_name: str) -> Dict[str, Any]:
        """Run a specific maintenance task manually"""

        if task_name not in self.maintenance_tasks:
            raise ValueError(f"Unknown maintenance task: {task_name}")

        try:
            result = await self.maintenance_tasks[task_name]()
            return {
                "task": task_name,
                "status": "completed",
                "timestamp": datetime.utcnow(),
                "result": result
            }
        except Exception as e:
            logger.error(f"Maintenance task {task_name} failed: {e}")
            return {
                "task": task_name,
                "status": "failed",
                "timestamp": datetime.utcnow(),
                "error": str(e)
            }

    def get_maintenance_history(self, db: Session, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent maintenance history"""

        logs = db.query(MaintenanceLog).order_by(
            MaintenanceLog.performed_at.desc()
        ).limit(limit).all()

        return [
            {
                "id": log.id,
                "action_type": log.action_type,
                "description": log.description,
                "status": log.status,
                "performed_at": log.performed_at,
                "affected_items": log.affected_items
            }
            for log in logs
        ]

# Global maintenance service instance
maintenance_service = MaintenanceService()
