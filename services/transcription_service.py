
"""Transcription service for audio processing."""
import httpx
import asyncio
import json
from typing import Optional, Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session
import logging

from models.database import Interview
from config.settings import settings

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for audio transcription using Sonix API."""
    
    def __init__(self):
        """Initialize transcription service."""
        self.api_key = settings.sonix_api_key
        self.base_url = "https://api.sonix.ai/v1"
        self.enabled = bool(self.api_key)
        
        if not self.enabled:
            logger.warning("Sonix API key not configured - transcription service disabled")

    async def upload_and_transcribe(self, audio_file_path: str, interview_id: int, db: Session) -> str:
        """Upload audio file to Sonix and start transcription."""
        
        if not self.enabled:
            raise RuntimeError("Transcription service is not configured")
        
        if not Path(audio_file_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        # Get interview
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise ValueError(f"Interview not found with id: {interview_id}")

        try:
            # Upload file to Sonix
            job_id = await self._upload_file(audio_file_path)

            # Update interview with status
            interview.transcription_status = "processing"
            db.commit()

            logger.info(f"Transcription started for interview {interview_id}, job_id: {job_id}")
            return job_id

        except Exception as e:
            logger.error(f"Transcription upload failed: {e}")
            interview.transcription_status = "failed"
            db.commit()
            raise

    async def _upload_file(self, audio_file_path: str) -> str:
        """Upload audio file to Sonix."""
        
        upload_url = f"{self.base_url}/media"

        try:
            with open(audio_file_path, 'rb') as audio_file:
                files = {
                    'file': (Path(audio_file_path).name, audio_file, 'audio/wav')
                }

                data = {
                    'name': Path(audio_file_path).name,
                    'language': 'en',
                    'model': 'automatic',
                    'punctuation': True,
                    'speaker_labels': True,
                    'custom_vocabulary': json.dumps([
                        'SOP', 'BMP', 'preventative maintenance', 'continuity', 'organizational'
                    ])
                }

                async with httpx.AsyncClient(timeout=300.0) as client:
                    response = await client.post(
                        upload_url,
                        files=files,
                        data=data,
                        headers={"Authorization": f"Bearer {self.api_key}"}
                    )

                    response.raise_for_status()
                    result = response.json()
                    return result['id']
        except httpx.HTTPError as e:
            logger.error(f"HTTP error uploading file: {e}")
            raise
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            raise

    async def check_transcription_status(self, job_id: str) -> Dict[str, Any]:
        """Check the status of a transcription job."""
        
        if not self.enabled:
            raise RuntimeError("Transcription service is not configured")
        
        status_url = f"{self.base_url}/media/{job_id}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    status_url,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error checking transcription status: {e}")
            raise

    async def get_transcript(self, job_id: str) -> str:
        """Get the completed transcript."""
        
        if not self.enabled:
            raise RuntimeError("Transcription service is not configured")
        
        transcript_url = f"{self.base_url}/media/{job_id}/transcript"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    transcript_url,
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                response.raise_for_status()

                transcript_data = response.json()

                # Extract text from the transcript
                if 'monologues' in transcript_data:
                    transcript_text = ""
                    for monologue in transcript_data['monologues']:
                        speaker = monologue.get('speaker', 'Unknown')
                        for element in monologue.get('elements', []):
                            if element.get('type') == 'text':
                                if not transcript_text or not transcript_text.endswith(f"{speaker}: "):
                                    transcript_text += f"\n{speaker}: "
                                transcript_text += element.get('value', '') + " "
                    return transcript_text.strip()
                else:
                    return transcript_data.get('text', '')
        except Exception as e:
            logger.error(f"Error getting transcript: {e}")
            raise

    async def process_completed_transcriptions(self, db: Session):
        """Check for completed transcriptions and update database."""
        
        if not self.enabled:
            logger.warning("Transcription service not enabled, skipping processing")
            return

        processing_interviews = db.query(Interview).filter(
            Interview.transcription_status == "processing"
        ).all()

        for interview in processing_interviews:
            try:
                # Note: This assumes transcription_job_id field exists
                # You may need to add this field to the Interview model
                job_id = getattr(interview, 'transcription_job_id', None)
                if not job_id:
                    continue
                
                status_info = await self.check_transcription_status(job_id)

                if status_info.get('status') == 'completed':
                    transcript = await self.get_transcript(job_id)
                    interview.transcription_text = transcript
                    interview.transcription_status = "completed"
                    db.commit()
                    logger.info(f"Transcription completed for interview {interview.id}")

                elif status_info.get('status') == 'failed':
                    interview.transcription_status = "failed"
                    db.commit()
                    logger.warning(f"Transcription failed for interview {interview.id}")

            except Exception as e:
                logger.error(f"Error processing transcription for interview {interview.id}: {e}")
                continue

    def _format_time(self, seconds: float) -> str:
        """Format seconds to MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"


# Global transcription service instance
transcription_service = TranscriptionService()
