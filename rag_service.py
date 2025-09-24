import json
import uuid
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
import numpy as np
import pinecone
from sqlalchemy.orm import Session
from models.database import Document, KnowledgeReport, ChatSession, ChatMessage, User
from config.settings import settings
from anthropic import Anthropic
import openai

class RAGService:
    def __init__(self):
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Initialize vector database (Pinecone)
        self.use_pinecone = settings.pinecone_api_key is not None
        if self.use_pinecone:
            pinecone.init(api_key=settings.pinecone_api_key, environment="us-east1-aws")
            self.index_name = "knowledge-capture"

            # Create index if it doesn't exist
            if self.index_name not in pinecone.list_indexes():
                pinecone.create_index(
                    name=self.index_name,
                    dimension=384,  # all-MiniLM-L6-v2 dimension
                    metric="cosine"
                )

            self.index = pinecone.Index(self.index_name)
        else:
            # Fallback to in-memory vector storage
            self.vectors = {}
            self.metadata = {}

        # Initialize LLM clients
        self.anthropic = Anthropic(api_key=settings.anthropic_api_key)
        openai.api_key = settings.openai_api_key

    def chunk_text(self, text: str, chunk_size: int = 512, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)

            if i + chunk_size >= len(words):
                break

        return chunks

    async def index_document(self, document: Document):
        """Index a document for RAG retrieval"""

        # Chunk the document content
        chunks = self.chunk_text(document.content_text)

        # Generate embeddings and store
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
                "source": f"{document.original_filename} (Page {i+1})"
            }

            if self.use_pinecone:
                self.index.upsert([(vector_id, embedding, metadata)])
            else:
                self.vectors[vector_id] = np.array(embedding)
                self.metadata[vector_id] = metadata

    async def index_knowledge_report(self, report: KnowledgeReport):
        """Index a knowledge report for RAG retrieval"""

        # Chunk the report content
        chunks = self.chunk_text(report.content)

        # Also index structured data
        if report.structured_data:
            structured_text = json.dumps(report.structured_data, indent=2)
            chunks.extend(self.chunk_text(structured_text))

        # Generate embeddings and store
        for i, chunk in enumerate(chunks):
            embedding = self.embedding_model.encode(chunk).tolist()

            vector_id = f"report_{report.id}_chunk_{i}"
            metadata = {
                "report_id": report.id,
                "document_type": "knowledge_report",
                "job_role": report.job_role.title if report.job_role else "Unknown",
                "chunk_index": i,
                "content": chunk,
                "source": f"Knowledge Report: {report.title}"
            }

            if self.use_pinecone:
                self.index.upsert([(vector_id, embedding, metadata)])
            else:
                self.vectors[vector_id] = np.array(embedding)
                self.metadata[vector_id] = metadata

    async def index_flat_file_content(self, file_id: str, content: str, filename: str):
        """Index uploaded flat file content for chat"""

        # Chunk the file content
        chunks = self.chunk_text(content)

        # Generate embeddings and store
        for i, chunk in enumerate(chunks):
            embedding = self.embedding_model.encode(chunk).tolist()

            vector_id = f"flat_file_{file_id}_chunk_{i}"
            metadata = {
                "file_id": file_id,
                "document_type": "flat_file",
                "filename": filename,
                "chunk_index": i,
                "content": chunk,
                "source": f"Uploaded File: {filename}"
            }

            if self.use_pinecone:
                self.index.upsert([(vector_id, embedding, metadata)])
            else:
                self.vectors[vector_id] = np.array(embedding)
                self.metadata[vector_id] = metadata

    def search_similar_content(self, query: str, top_k: int = 5, file_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for similar content using vector similarity"""

        # Generate query embedding
        query_embedding = self.embedding_model.encode(query)

        if self.use_pinecone:
            # Build filter for specific file if provided
            filter_dict = {}
            if file_id:
                filter_dict = {"file_id": file_id}

            # Search in Pinecone
            results = self.index.query(
                vector=query_embedding.tolist(),
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict if filter_dict else None
            )

            return [
                {
                    "content": match.metadata["content"],
                    "source": match.metadata["source"],
                    "score": match.score,
                    "metadata": match.metadata
                }
                for match in results.matches
            ]
        else:
            # Fallback in-memory search
            similarities = []
            for vector_id, vector in self.vectors.items():
                # Apply file filter if specified
                if file_id and self.metadata[vector_id].get("file_id") != file_id:
                    continue

                similarity = np.dot(query_embedding, vector) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(vector)
                )
                similarities.append((vector_id, similarity))

            # Sort by similarity and return top_k
            similarities.sort(key=lambda x: x[1], reverse=True)

            return [
                {
                    "content": self.metadata[vector_id]["content"],
                    "source": self.metadata[vector_id]["source"],
                    "score": similarity,
                    "metadata": self.metadata[vector_id]
                }
                for vector_id, similarity in similarities[:top_k]
            ]

    async def chat_with_knowledge_base(
        self, 
        query: str, 
        user: User, 
        session_id: Optional[str] = None,
        file_id: Optional[str] = None,
        db: Session = None
    ) -> Tuple[str, str, List[Dict[str, Any]]]:
        """Chat with the knowledge base using RAG"""

        # Create or get chat session
        if not session_id:
            session_id = str(uuid.uuid4())
            if db:
                chat_session = ChatSession(
                    user_id=user.id,
                    session_id=session_id
                )
                db.add(chat_session)
                db.commit()

        # Search for relevant content
        relevant_docs = self.search_similar_content(query, top_k=5, file_id=file_id)

        # Build context from retrieved documents
        context = ""
        sources = []
        for i, doc in enumerate(relevant_docs):
            context += f"[Source {i+1}: {doc['source']}]\n{doc['content']}\n\n"
            sources.append({
                "source": doc["source"],
                "content": doc["content"][:200] + "...",
                "score": doc["score"]
            })

        # Get conversation history
        conversation_history = ""
        if db:
            recent_messages = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id
            ).order_by(ChatMessage.timestamp.desc()).limit(6).all()

            for msg in reversed(recent_messages):
                conversation_history += f"{msg.message_type}: {msg.content}\n"

        # Build prompt for LLM
        if file_id:
            system_prompt = f"""You are a helpful assistant that answers questions based on the content of an uploaded file. 
            Use the provided context to answer the user's question accurately and helpfully.

            If the answer is not in the provided context, say so clearly.
            Always cite the source when providing information.
            """
        else:
            system_prompt = f"""You are a helpful assistant for an organizational knowledge management system.
            You help employees find information about procedures, roles, contacts, and organizational knowledge.

            Use the provided context from documents and knowledge reports to answer questions.
            If you don't have enough information to answer completely, say so and suggest what additional information might be helpful.
            Always cite your sources when providing information.
            """

        prompt = f"""Context from knowledge base:
        {context}

        Previous conversation:
        {conversation_history}

        User question: {query}

        Please provide a helpful response based on the context above. Include relevant source citations.
        """

        try:
            # Use Anthropic for response generation
            response = self.anthropic.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                system=system_prompt,
                messages=[{"role": "user", "content": prompt}]
            )

            answer = response.content[0].text

            # Save messages to database
            if db:
                # Save user message
                user_message = ChatMessage(
                    session_id=session_id,
                    message_type="user",
                    content=query
                )
                db.add(user_message)

                # Save assistant message
                assistant_message = ChatMessage(
                    session_id=session_id,
                    message_type="assistant",
                    content=answer,
                    sources=sources
                )
                db.add(assistant_message)
                db.commit()

            return answer, session_id, sources

        except Exception as e:
            error_msg = f"I apologize, but I encountered an error while processing your question: {str(e)}"
            return error_msg, session_id, sources

    async def reindex_all_content(self, db: Session):
        """Reindex all documents and knowledge reports"""

        # Clear existing index
        if self.use_pinecone:
            self.index.delete(delete_all=True)
        else:
            self.vectors.clear()
            self.metadata.clear()

        # Reindex all documents
        documents = db.query(Document).all()
        for doc in documents:
            await self.index_document(doc)

        # Reindex all knowledge reports
        reports = db.query(KnowledgeReport).all()
        for report in reports:
            await self.index_knowledge_report(report)

    def get_chat_history(self, session_id: str, db: Session) -> List[Dict[str, Any]]:
        """Get chat history for a session"""

        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp).all()

        return [
            {
                "type": msg.message_type,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "sources": msg.sources
            }
            for msg in messages
        ]

# Global RAG service instance
rag_service = RAGService()
