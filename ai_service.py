import json
from typing import List, Dict, Any, Optional
from anthropic import Anthropic
import openai
from sqlalchemy.orm import Session
from models.database import Document, Interview, KnowledgeReport, JobRole
from config.settings import settings

class AIService:
    def __init__(self):
        self.anthropic = Anthropic(api_key=settings.anthropic_api_key)
        openai.api_key = settings.openai_api_key

    async def generate_interview_questions(
        self, 
        job_role: str, 
        job_description: str, 
        related_documents: List[Document]
    ) -> List[str]:
        """Generate interview questions based on job role and documents"""

        # Prepare document context
        document_context = ""
        for doc in related_documents[:10]:  # Limit to prevent token overflow
            document_context += f"Document: {doc.original_filename}\n"
            document_context += f"Content: {doc.content_text[:1000]}...\n\n"

        prompt = f"""You are an expert in organizational knowledge management and continuity planning. 

        Job Role: {job_role}
        Job Description: {job_description}

        Related Organizational Documents:
        {document_context}

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

        Format your response as a JSON list of questions.
        """

        try:
            response = self.anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse the response to extract questions
            content = response.content[0].text

            # Try to extract JSON from the response
            start_idx = content.find('[')
            end_idx = content.rfind(']') + 1

            if start_idx != -1 and end_idx != -1:
                questions_json = content[start_idx:end_idx]
                questions = json.loads(questions_json)
                return questions
            else:
                # Fallback: split by lines and clean up
                lines = content.split('\n')
                questions = []
                for line in lines:
                    line = line.strip()
                    if line and (line.startswith('-') or line.startswith('*') or '?' in line):
                        # Clean up formatting
                        question = line.lstrip('- *').strip()
                        if question:
                            questions.append(question)
                return questions[:20]  # Limit to 20 questions

        except Exception as e:
            print(f"Error generating questions with Anthropic: {e}")
            # Fallback generic questions
            return self._get_generic_questions(job_role)

    def _get_generic_questions(self, job_role: str) -> List[str]:
        """Fallback generic questions if AI generation fails"""
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
        ]

    async def generate_knowledge_report(
        self,
        job_role: JobRole,
        interview: Interview,
        related_documents: List[Document],
        db: Session
    ) -> Dict[str, Any]:
        """Generate comprehensive knowledge report from interview and documents"""

        # Prepare document context
        document_context = ""
        for doc in related_documents:
            document_context += f"Document: {doc.original_filename}\n"
            document_context += f"Type: {doc.file_type} - {doc.document_category}\n"
            document_context += f"Content: {doc.content_text[:1500]}\n\n"

        prompt = f"""You are creating a comprehensive knowledge transfer report for organizational continuity.

        Job Role: {job_role.title}
        Department: {job_role.department}
        Job Description: {job_role.description}

        Interview Transcript:
        {interview.transcript}

        Related Organizational Documents:
        {document_context}

        Create a comprehensive knowledge transfer report with the following structure:

        # {job_role.title} - Knowledge Transfer Report

        ## Executive Summary
        [Brief overview of the role and key findings]

        ## Job Description and Responsibilities
        [Detailed breakdown of duties and responsibilities]

        ## Standard Operating Procedures
        [Both documented and undocumented procedures]

        ## Key Relationships and Contacts
        [Internal and external relationships critical to the role]

        ## Tools, Systems, and Resources
        [Technology, equipment, and resources used]

        ## Historical Context and Institutional Knowledge
        [Background information and context not found in documents]

        ## Common Challenges and Solutions
        [Frequent problems and how they're resolved]

        ## Seasonal and Periodic Activities
        [Time-sensitive tasks and cyclical responsibilities]

        ## Emergency Procedures and Contingencies
        [Crisis management and backup procedures]

        ## Budget and Resource Management
        [Financial considerations and resource allocation]

        ## Training and Onboarding Recommendations
        [What new employees need to know]

        ## SWOT Analysis
        [Strengths, Weaknesses, Opportunities, Threats for this role]

        ## Critical Knowledge Gaps
        [Important information that needs documentation or clarification]

        ## Recommendations for Continuity
        [Steps to ensure smooth transitions and operations]

        Please ensure the report is detailed, actionable, and serves as a comprehensive guide for continuity planning and onboarding.
        """

        try:
            response = self.anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}]
            )

            report_content = response.content[0].text

            # Extract SWOT analysis for structured storage
            swot_analysis = self._extract_swot_from_report(report_content)

            # Create structured data for RAG
            structured_data = {
                "job_title": job_role.title,
                "department": job_role.department,
                "key_responsibilities": self._extract_responsibilities(report_content),
                "key_contacts": self._extract_contacts(report_content),
                "critical_procedures": self._extract_procedures(report_content),
                "tools_and_systems": self._extract_tools(report_content),
                "interview_insights": interview.transcript,
                "document_references": [{"id": doc.id, "filename": doc.original_filename} for doc in related_documents]
            }

            return {
                "content": report_content,
                "swot_analysis": swot_analysis,
                "structured_data": structured_data
            }

        except Exception as e:
            print(f"Error generating report: {e}")
            raise Exception(f"Failed to generate knowledge report: {str(e)}")

    def _extract_swot_from_report(self, report_content: str) -> Dict[str, List[str]]:
        """Extract SWOT analysis from report content"""
        # Simple extraction - could be enhanced with NLP
        swot = {
            "strengths": [],
            "weaknesses": [],
            "opportunities": [],
            "threats": []
        }

        lines = report_content.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if 'Strengths' in line and '##' in line:
                current_section = 'strengths'
            elif 'Weaknesses' in line and '##' in line:
                current_section = 'weaknesses'
            elif 'Opportunities' in line and '##' in line:
                current_section = 'opportunities'
            elif 'Threats' in line and '##' in line:
                current_section = 'threats'
            elif line.startswith('##') or line.startswith('#'):
                current_section = None
            elif current_section and line and (line.startswith('-') or line.startswith('*')):
                item = line.lstrip('- *').strip()
                if item:
                    swot[current_section].append(item)

        return swot

    def _extract_responsibilities(self, report_content: str) -> List[str]:
        """Extract key responsibilities from report"""
        # Simple extraction - could be enhanced
        responsibilities = []
        lines = report_content.split('\n')
        in_responsibilities_section = False

        for line in lines:
            line = line.strip()
            if 'Responsibilities' in line and '##' in line:
                in_responsibilities_section = True
            elif line.startswith('##') and in_responsibilities_section:
                break
            elif in_responsibilities_section and line and (line.startswith('-') or line.startswith('*')):
                item = line.lstrip('- *').strip()
                if item:
                    responsibilities.append(item)

        return responsibilities

    def _extract_contacts(self, report_content: str) -> List[str]:
        """Extract key contacts from report"""
        contacts = []
        lines = report_content.split('\n')
        in_contacts_section = False

        for line in lines:
            line = line.strip()
            if 'Contacts' in line and '##' in line:
                in_contacts_section = True
            elif line.startswith('##') and in_contacts_section:
                break
            elif in_contacts_section and line and (line.startswith('-') or line.startswith('*')):
                item = line.lstrip('- *').strip()
                if item:
                    contacts.append(item)

        return contacts

    def _extract_procedures(self, report_content: str) -> List[str]:
        """Extract key procedures from report"""
        procedures = []
        lines = report_content.split('\n')
        in_procedures_section = False

        for line in lines:
            line = line.strip()
            if 'Procedures' in line and '##' in line:
                in_procedures_section = True
            elif line.startswith('##') and in_procedures_section:
                break
            elif in_procedures_section and line and (line.startswith('-') or line.startswith('*')):
                item = line.lstrip('- *').strip()
                if item:
                    procedures.append(item)

        return procedures

    def _extract_tools(self, report_content: str) -> List[str]:
        """Extract tools and systems from report"""
        tools = []
        lines = report_content.split('\n')
        in_tools_section = False

        for line in lines:
            line = line.strip()
            if ('Tools' in line or 'Systems' in line) and '##' in line:
                in_tools_section = True
            elif line.startswith('##') and in_tools_section:
                break
            elif in_tools_section and line and (line.startswith('-') or line.startswith('*')):
                item = line.lstrip('- *').strip()
                if item:
                    tools.append(item)

        return tools

# Global AI service instance
ai_service = AIService()
