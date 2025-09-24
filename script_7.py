# Create transcription service for Sonix API integration
transcription_service_content = """import httpx
import asyncio
import json
from typing import Optional, Dict, Any
from pathlib import Path
from sqlalchemy.orm import Session
from models.database import Interview
from config.settings import settings

class TranscriptionService:
    def __init__(self):
        self.api_key = settings.sonix_api_key
        self.base_url = "https://api.sonix.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def upload_and_transcribe(self, audio_file_path: str, interview_id: int, db: Session) -> str:
        \"\"\"Upload audio file to Sonix and start transcription\"\"\"
        
        if not Path(audio_file_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        # Update interview status
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise ValueError(f"Interview not found with id: {interview_id}")
        
        try:
            # Upload file to Sonix
            job_id = await self._upload_file(audio_file_path)
            
            # Update interview with job ID and status
            interview.transcription_job_id = job_id
            interview.transcription_status = "processing"
            db.commit()
            
            return job_id
            
        except Exception as e:
            interview.transcription_status = "failed"
            db.commit()
            raise Exception(f"Transcription upload failed: {str(e)}")
    
    async def _upload_file(self, audio_file_path: str) -> str:
        \"\"\"Upload audio file to Sonix\"\"\"
        
        upload_url = f"{self.base_url}/media"
        
        # Prepare file for upload
        with open(audio_file_path, 'rb') as audio_file:
            files = {
                'file': (Path(audio_file_path).name, audio_file, 'audio/wav')
            }
            
            # Prepare form data
            data = {
                'name': Path(audio_file_path).name,
                'language': 'en',  # Default to English, could be configurable
                'model': 'automatic',
                'punctuation': True,
                'speaker_labels': True,  # Enable speaker identification
                'custom_vocabulary': json.dumps([
                    'SOP', 'BMP', 'preventative maintenance', 'continuity', 'organizational'
                ])  # Custom vocabulary for better accuracy
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
    
    async def check_transcription_status(self, job_id: str) -> Dict[str, Any]:
        \"\"\"Check the status of a transcription job\"\"\"
        
        status_url = f"{self.base_url}/media/{job_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(status_url, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def get_transcript(self, job_id: str) -> str:
        \"\"\"Get the completed transcript\"\"\"
        
        transcript_url = f"{self.base_url}/media/{job_id}/transcript"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(transcript_url, headers=self.headers)
            response.raise_for_status()
            
            # Sonix returns various formats, we'll get the text format
            transcript_data = response.json()
            
            # Extract text from the transcript
            if 'monologues' in transcript_data:
                transcript_text = ""
                for monologue in transcript_data['monologues']:
                    speaker = monologue.get('speaker', 'Unknown')
                    for element in monologue.get('elements', []):
                        if element.get('type') == 'text':
                            if not transcript_text or not transcript_text.endswith(f"{speaker}: "):
                                transcript_text += f"\\n{speaker}: "
                            transcript_text += element.get('value', '') + " "
                return transcript_text.strip()
            else:
                # Fallback to simple text extraction
                return transcript_data.get('text', '')
    
    async def process_completed_transcriptions(self, db: Session):
        \"\"\"Check for completed transcriptions and update database\"\"\"
        
        # Get all interviews with processing status
        processing_interviews = db.query(Interview).filter(
            Interview.transcription_status == "processing"
        ).all()
        
        for interview in processing_interviews:
            if interview.transcription_job_id:
                try:
                    # Check status
                    status_info = await self.check_transcription_status(interview.transcription_job_id)
                    
                    if status_info.get('status') == 'completed':
                        # Get transcript
                        transcript = await self.get_transcript(interview.transcription_job_id)
                        
                        # Update interview
                        interview.transcript = transcript
                        interview.transcription_status = "completed"
                        
                        # Extract duration if available
                        if 'duration' in status_info:
                            interview.duration_minutes = int(status_info['duration'] / 60)
                        
                        db.commit()
                        
                    elif status_info.get('status') == 'failed':
                        interview.transcription_status = "failed"
                        db.commit()
                        
                except Exception as e:
                    print(f"Error processing transcription for interview {interview.id}: {e}")
                    continue
    
    async def get_transcription_with_timestamps(self, job_id: str) -> Dict[str, Any]:
        \"\"\"Get transcript with detailed timestamps and speaker information\"\"\"
        
        transcript_url = f"{self.base_url}/media/{job_id}/transcript"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(transcript_url, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    def format_transcript_for_analysis(self, transcript_data: Dict[str, Any]) -> str:
        \"\"\"Format transcript data for AI analysis with speaker labels and timestamps\"\"\"
        
        formatted_transcript = ""
        
        if 'monologues' in transcript_data:
            for monologue in transcript_data['monologues']:
                speaker = monologue.get('speaker', 'Unknown')
                start_time = monologue.get('start', 0)
                
                formatted_transcript += f"\\n[{self._format_time(start_time)}] {speaker}: "
                
                for element in monologue.get('elements', []):
                    if element.get('type') == 'text':
                        formatted_transcript += element.get('value', '') + " "
                
                formatted_transcript += "\\n"
        
        return formatted_transcript.strip()
    
    def _format_time(self, seconds: float) -> str:
        \"\"\"Format seconds to MM:SS\"\"\"
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
    
    async def delete_transcription(self, job_id: str):
        \"\"\"Delete a transcription job from Sonix (for cleanup)\"\"\"
        
        delete_url = f"{self.base_url}/media/{job_id}"
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(delete_url, headers=self.headers)
            response.raise_for_status()

# Global transcription service instance
transcription_service = TranscriptionService()
"""

with open("knowledge_capture_mvp/services/transcription_service.py", "w") as f:
    f.write(transcription_service_content)

print("Transcription service created!")
print("- services/transcription_service.py")