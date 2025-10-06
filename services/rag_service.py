
"""RAG (Retrieval Augmented Generation) service for chatbot."""
import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
import logging

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    from pinecone import Pinecone
except ImportError:
    Pinecone = None

from sqlalchemy.orm import Session
from models.database import Document, KnowledgeReport, ChatSession, ChatMessage, User
from config.settings import settings

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG-based chatbot functionality."""
    
    def __init__(self):
        """Initialize RAG service."""
        self.embedding_model = None
        self.use_pinecone = False
        self.index = None
        self.vectors = {}
        self.metadata = {}
        self.anthropic_client = None
        self.openai_client = None
        
        # Initialize embedding model
        if SentenceTransformer and np:
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Embedding model initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize embedding model: {e}")
        else:
            logger.warning("sentence-transformers or numpy not available")

        # Initialize vector database (Pinecone)
        if settings.pinecone_api_key and Pinecone:
            try:
                pc = Pinecone(api_key=settings.pinecone_api_key)
                self.index_name = "pipewrench-knowledge"
                
                # Check if index exists
                existing_indexes = pc.list_indexes()
                if self.index_name not in [idx.name for idx in existing_indexes]:
                    pc.create_index(
                        name=self.index_name,
                        dimension=384,
                        metric="cosine"
                    )
                
                self.index = pc.Index(self.index_name)
                self.use_pinecone = True
                logger.info("Pinecone vector database initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Pinecone: {e}")
        else:
            logger.info("Using in-memory vector storage (Pinecone not configured)")

        # Initialize LLM clients
        if settings.anthropic_api_key and Anthropic:
            try:
                self.anthropic_client = Anthropic(api_key=settings.anthropic_api_key)
                logger.info("Anthropic client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic: {e}")
        
        if settings.openai_api_key and OpenAI:
            try:
                self.openai_client = OpenAI(api_key=settings.openai_api_key)
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")

    def chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        if not text:
            return []
        
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)

            if i + chunk_size >= len(words):
                break

        return chunks

    async def index_document(self, document: Document):
        """Index a document for RAG retrieval."""
        
        if not self.embedding_model:
            logger.warning("Embedding model not available, skipping indexing")
            return
        
        if not document.content_text:
            logger.warning(f"Document {document.id} has no content to index")
            return

        try:
            chunks = self.chunk_text(document.content_text)

            for i, chunk in enumerate(chunks):
                embedding = self.embedding_model.encode(chunk).tolist()

                vector_id = f"doc_{document.id}_chunk_{i}"
                metadata = {
                    "document_id": document.id,
                    "document_type": "document",
                    "filename": document.original_filename,
                    "file_type": document.file_type,
                    "chunk_index": i,
                    "content": chunk,
                    "source": f"{document.original_filename} (Chunk {i+1})"
                }

                if self.use_pinecone and self.index:
                    self.index.upsert([(vector_id, embedding, metadata)])
                else:
                    self.vectors[vector_id] = np.array(embedding) if np else embedding
                    self.metadata[vector_id] = metadata

            logger.info(f"Indexed document {document.id} with {len(chunks)} chunks")
        except Exception as e:
            logger.error(f"Error indexing document {document.id}: {e}")
            raise

    async def index_knowledge_report(self, report: KnowledgeReport):
        """Index a knowledge report for RAG retrieval."""
        
        if not self.embedding_model:
            logger.warning("Embedding model not available, skipping indexing")
            return

        try:
            chunks = self.chunk_text(report.content)

            # Also index structured data if available
            if report.swot_analysis:
                structured_text = json.dumps(report.swot_analysis, indent=2)
                chunks.extend(self.chunk_text(structured_text))

            for i, chunk in enumerate(chunks):
                embedding = self.embedding_model.encode(chunk).tolist()

                vector_id = f"report_{report.id}_chunk_{i}"
                metadata = {
                    "report_id": report.id,
                    "document_type": "knowledge_report",
                    "title": report.title,
                    "chunk_index": i,
                    "content": chunk,
                    "source": f"{report.title} (Chunk {i+1})"
                }

                if self.use_pinecone and self.index:
                    self.index.upsert([(vector_id, embedding, metadata)])
                else:
                    self.vectors[vector_id] = np.array(embedding) if np else embedding
                    self.metadata[vector_id] = metadata

            logger.info(f"Indexed knowledge report {report.id} with {len(chunks)} chunks")
        except Exception as e:
            logger.error(f"Error indexing knowledge report {report.id}: {e}")
            raise

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents using vector similarity."""
        
        if not self.embedding_model:
            logger.warning("Embedding model not available")
            return []

        try:
            query_embedding = self.embedding_model.encode(query).tolist()

            if self.use_pinecone and self.index:
                results = self.index.query(
                    vector=query_embedding,
                    top_k=top_k,
                    include_metadata=True
                )
                return [
                    {
                        "score": match.score,
                        "content": match.metadata.get("content", ""),
                        "source": match.metadata.get("source", "Unknown"),
                        "metadata": match.metadata
                    }
                    for match in results.matches
                ]
            else:
                # In-memory search
                if not self.vectors:
                    return []
                
                if not np:
                    logger.warning("NumPy not available for similarity calculation")
                    return []
                
                query_vec = np.array(query_embedding)
                similarities = {}
                
                for vec_id, vec in self.vectors.items():
                    similarity = np.dot(query_vec, vec) / (np.linalg.norm(query_vec) * np.linalg.norm(vec))
                    similarities[vec_id] = similarity
                
                top_ids = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:top_k]
                
                return [
                    {
                        "score": score,
                        "content": self.metadata[vec_id].get("content", ""),
                        "source": self.metadata[vec_id].get("source", "Unknown"),
                        "metadata": self.metadata[vec_id]
                    }
                    for vec_id, score in top_ids
                ]
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []

    async def chat(
        self,
        message: str,
        session_id: Optional[str],
        user: User,
        db: Session
    ) -> Tuple[str, str, List[Dict[str, Any]]]:
        """Process a chat message with RAG."""
        
        # Create or get session
        if not session_id:
            session_id = str(uuid.uuid4())
            session = ChatSession(
                session_id=session_id,
                user_id=user.id,
                title=message[:50]
            )
            db.add(session)
            db.commit()
        else:
            session = db.query(ChatSession).filter(
                ChatSession.session_id == session_id
            ).first()
            if not session:
                raise ValueError(f"Session not found: {session_id}")

        # Search for relevant context
        search_results = await self.search(message, top_k=5)
        
        # Build context from search results
        context = "\n\n".join([
            f"Source: {result['source']}\nContent: {result['content']}"
            for result in search_results
        ])

        # Generate response
        response_text = await self._generate_response(message, context, session, db)

        # Save messages
        user_message = ChatMessage(
            session_id=session.id,
            role="user",
            content=message
        )
        assistant_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=response_text,
            sources=[{"source": r["source"], "score": r["score"]} for r in search_results]
        )
        
        db.add(user_message)
        db.add(assistant_message)
        db.commit()

        return response_text, session_id, search_results

    async def _generate_response(
        self,
        message: str,
        context: str,
        session: ChatSession,
        db: Session
    ) -> str:
        """Generate a response using LLM."""
        
        # Get conversation history
        history = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at.desc()).limit(10).all()
        
        history_text = "\n".join([
            f"{msg.role}: {msg.content}"
            for msg in reversed(history)
        ])

        prompt = f"""You are a helpful AI assistant with access to organizational knowledge.

Context from knowledge base:
{context}

Conversation history:
{history_text}

User: {message}

Provide a helpful, accurate response based on the context provided. If the context doesn't contain relevant information, say so and provide general guidance."""

        try:
            if self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            elif self.openai_client:
                response = self.openai_client.chat.completions.create(
                    model=settings.default_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000,
                    temperature=0.7
                )
                return response.choices[0].message.content
            else:
                return "I apologize, but the AI service is not currently available. Please try again later."
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I encountered an error generating a response. Please try again."


# Global RAG service instance
rag_service = RAGService()
