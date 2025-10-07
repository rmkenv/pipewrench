
"""AI service for LLM interactions."""
import json
from typing import List, Dict, Any, Optional
import logging

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from sqlalchemy.orm import Session
from models.database import Document, Interview, KnowledgeReport, JobRole
from config.settings import settings

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI/LLM operations."""
    
    def __init__(self):
        """Initialize AI service with API clients."""
        self.anthropic_client = None
        self.openai_client = None
        
        if settings.anthropic_api_key and Anthropic:
            try:
                self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
                logger.info("Anthropic client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")
        
        if settings.openai_api_key and OpenAI:
            try:
                self.openai_client = OpenAI(api_key=settings.openai_api_key)
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")

    async def generate_interview_questions(
        self, 
        job_role: str, 
        job_description: str, 
        related_documents: List[Document]
    ) -> List[str]:
        """Generate interview questions based on job role and documents."""
        
        if not job_role:
            raise ValueError("Job role is required")
        
        # Prepare document context
        document_context = ""
        for doc in related_documents[:10]:  # Limit to prevent token overflow
            if doc.content_text:
                document_context += f"Document: {doc.original_filename}\n"
                document_context += f"Content: {doc.content_text[:1000]}...\n\n"

        prompt = f"""You are an expert in organizational knowledge management and continuity planning. 

Job Role: {job_role}
Job Description: {job_description or 'Not provided'}

Related Organizational Documents:
{document_context or 'No documents provided'}

Generate 15-20 thoughtful interview questions that will help capture critical institutional knowledge from an employee in this role. Focus on:

1. Historical context and decisions that aren't documented
2. Unwritten procedures and informal processes
3. Key relationships and communication patterns
4. Common problems and how they're typically resolved
5. Critical knowledge that would be lost if this person left
6. Seasonal or cyclical activities not obvious from documents
7. Emergency procedures and contingency plans
8. Vendor relationships and contacts
9. Budget considerations and resource allocation insights
10. Training and onboarding insights for future employees

Format your response as a JSON array of question strings.
"""

        try:
            if self.anthropic_client:
                return await self._generate_with_anthropic(prompt)
            elif self.openai_client:
                return await self._generate_with_openai(prompt)
            else:
                logger.warning("No AI client available, using generic questions")
                return self._get_generic_questions(job_role)
        except Exception as e:
            logger.error(f"Error generating questions: {e}")
            return self._get_generic_questions(job_role)

    async def _generate_with_anthropic(self, prompt: str) -> List[str]:
        """Generate questions using Anthropic Claude."""
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            
            # Try to extract JSON from the response
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1

            if start_idx != -1 and end_idx != -1:
                questions_json = content[start_idx:end_idx]
                questions = json.loads(questions_json)
                return questions[:20]
            else:
                # Fallback: parse line by line
                return self._parse_questions_from_text(content)

        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise

    async def _generate_with_openai(self, prompt: str) -> List[str]:
        """Generate questions using OpenAI GPT."""
        try:
            response = self.openai_client.chat.completions.create(
                model=settings.default_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.max_tokens,
                temperature=settings.temperature
            )

            content = response.choices[0].message.content
            
            # Try to extract JSON
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1

            if start_idx != -1 and end_idx != -1:
                questions_json = content[start_idx:end_idx]
                questions = json.loads(questions_json)
                return questions[:20]
            else:
                return self._parse_questions_from_text(content)

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise

    def _parse_questions_from_text(self, text: str) -> List[str]:
        """Parse questions from unstructured text."""
        lines = text.split('\n')
        questions = []
        for line in lines:
            line = line.strip()
            if line and (line.startswith('-') or line.startswith('*') or line.startswith(tuple(str(i) for i in range(1, 10))) or '?' in line):
                # Clean up formatting
                question = line.lstrip('- *0123456789.').strip()
                if question and '?' in question:
                    questions.append(question)
        return questions[:20]

    def _get_generic_questions(self, job_role: str) -> List[str]:
        """Fallback generic questions if AI generation fails."""
        return [
            f"What are the most critical tasks you perform in your role as {job_role}?",
            "What unwritten procedures do you follow that aren't in the official documentation?",
            "What are the biggest challenges you face in this role?",
            "Who are your key contacts and why are these relationships important?",
            "What would you want a replacement to know that isn't written down anywhere?",
            "What seasonal or periodic activities does this role involve?",
            "What are the most common problems that arise and how do you handle them?",
            "What emergency procedures should someone in this role know?",
            "What budget considerations are important for this position?",
            "What training would you recommend for someone new to this role?",
            "What tools and systems do you use daily?",
            "What are the most important deadlines or time-sensitive tasks?",
            "What institutional knowledge do you rely on that isn't documented?",
            "What would cause the most disruption if you were suddenly unavailable?",
            "What advice would you give to someone taking over this role?"
        ]

    async def generate_knowledge_report(
        self,
        job_role: JobRole,
        interviews: List[Interview],
        documents: List[Document],
        db: Session
    ) -> str:
        """Generate a comprehensive knowledge report."""
        
        if not interviews:
            raise ValueError("At least one interview is required")
        
        # Prepare context
        interview_context = ""
        for interview in interviews:
            if interview.transcription_text:
                interview_context += f"\n\nInterview with {interview.interviewee_user.full_name}:\n"
                interview_context += interview.transcription_text[:5000]  # Limit length
        
        document_context = ""
        for doc in documents[:5]:
            if doc.content_text:
                document_context += f"\n\nDocument: {doc.original_filename}\n"
                document_context += doc.content_text[:2000]
        
        prompt = f"""Generate a comprehensive knowledge report for the {job_role.title} role.

Job Description: {job_role.description or 'Not provided'}

Interview Transcripts:
{interview_context}

Related Documents:
{document_context}

Create a detailed report that includes:
1. Executive Summary
2. Role Overview
3. Key Responsibilities and Processes
4. Critical Knowledge and Insights
5. SWOT Analysis (Strengths, Weaknesses, Opportunities, Threats)
6. Recommendations for Knowledge Transfer
7. Training and Onboarding Suggestions

Format the report in markdown."""

        try:
            if self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4000,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            elif self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=settings.default_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4000,
                    temperature=0.7
                )
                return response.choices[0].message.content
            else:
                raise RuntimeError("No AI client available")
        except Exception as e:
            logger.error(f"Error generating knowledge report: {e}")
            raise


# Global instance
ai_service = AIService()
