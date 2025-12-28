"""Document processing and ingestion system"""

import hashlib
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from io import BytesIO

from openai import OpenAI

from src.knowledge.vector_store import get_vector_store, VectorStore
from src.database.database import get_db
from src.database.models import KnowledgeEntry
from src.utils.config import get_settings
from src.utils.errors import KnowledgeBaseError
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class DocumentProcessor:
    """Processes documents for knowledge base ingestion"""

    def __init__(self):
        """Initialize document processor"""
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.vector_store = get_vector_store()
        self.chunk_size = 1000  # Characters per chunk
        self.chunk_overlap = 200  # Overlap between chunks

    async def process_document(
        self,
        content: str,
        title: str,
        source: Optional[str] = None,
        source_type: Optional[str] = None,
        business_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        db: Optional[Any] = None,
        vendor: Optional[str] = None,
        doc_type: Optional[str] = None,
        api_version: Optional[str] = None,
        endpoint: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Process a document: chunk, embed, and store
        
        Args:
            content: Document content
            title: Document title
            source: Source URL or path
            source_type: Type of source (pdf, docx, txt, url)
            business_id: Business configuration ID
            metadata: Additional metadata
            db: Database session
            
        Returns:
            List of vector IDs created
        """
        try:
            # Chunk the document
            chunks = self._chunk_text(content)
            logger.info("document_chunked", title=title, chunks=len(chunks))

            # Generate embeddings
            embeddings = await self._generate_embeddings([chunk["text"] for chunk in chunks])
            logger.info("embeddings_generated", count=len(embeddings))

            # Prepare vectors for storage
            vector_ids = []
            vectors_data = []

            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = str(uuid.uuid4())
                vector_ids.append(vector_id)

                chunk_metadata = {
                    "title": title,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "source": source or "",
                    "source_type": source_type or "text",
                    "business_id": business_id or "",
                    **(metadata or {}),
                }

                vectors_data.append({
                    "vector": embedding,
                    "id": vector_id,
                    "metadata": chunk_metadata,
                })

            # Store in vector database
            await self.vector_store.initialize()
            await self.vector_store.upsert(
                vectors=[v["vector"] for v in vectors_data],
                ids=[v["id"] for v in vectors_data],
                metadata=[v["metadata"] for v in vectors_data],
                namespace=business_id,
            )

            # Store in database
            if db:
                from datetime import datetime
                knowledge_entry = KnowledgeEntry(
                    title=title,
                    content=content,
                    source=source,
                    source_type=source_type,
                    business_id=business_id,
                    vector_id=vector_ids[0] if vector_ids else None,  # Store first vector ID as reference
                    metadata=metadata or {},
                    vendor=vendor,
                    doc_type=doc_type,
                    api_version=api_version,
                    endpoint=endpoint,
                    tags=tags or [],
                    last_synced=datetime.utcnow() if vendor else None,  # Set sync time for documentation
                )
                db.add(knowledge_entry)
                db.commit()

            logger.info("document_processed", title=title, vector_ids=len(vector_ids))
            return vector_ids

        except Exception as e:
            logger.error("document_processing_error", error=str(e), title=title)
            raise KnowledgeBaseError(f"Failed to process document: {str(e)}") from e

    def _chunk_text(self, text: str) -> List[Dict[str, str]]:
        """
        Chunk text into smaller pieces
        
        Args:
            text: Text to chunk
            
        Returns:
            List of chunk dictionaries with text and metadata
        """
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                last_period = chunk_text.rfind(".")
                last_newline = chunk_text.rfind("\n")
                break_point = max(last_period, last_newline)

                if break_point > self.chunk_size * 0.5:  # Only break if we're past halfway
                    chunk_text = text[start:start + break_point + 1]
                    end = start + break_point + 1

            chunks.append({
                "text": chunk_text.strip(),
                "start": start,
                "end": end,
                "index": chunk_index,
            })

            # Move start position with overlap
            start = end - self.chunk_overlap
            chunk_index += 1

        return chunks

    async def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts using OpenAI
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=texts,
            )

            return [item.embedding for item in response.data]

        except Exception as e:
            logger.error("embedding_generation_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to generate embeddings: {str(e)}") from e

    async def process_file(
        self,
        file_path: str,
        business_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        db: Optional[Any] = None,
    ) -> List[str]:
        """
        Process a file (PDF, DOCX, TXT)
        
        Args:
            file_path: Path to file
            business_id: Business configuration ID
            metadata: Additional metadata
            db: Database session
            
        Returns:
            List of vector IDs created
        """
        path = Path(file_path)
        source_type = path.suffix[1:].lower()  # Remove dot

        try:
            # Extract text based on file type
            if source_type == "pdf":
                content, title = self._extract_pdf(file_path)
            elif source_type in ["doc", "docx"]:
                content, title = self._extract_docx(file_path)
            elif source_type == "txt":
                content, title = self._extract_txt(file_path)
            else:
                raise KnowledgeBaseError(f"Unsupported file type: {source_type}")

            return await self.process_document(
                content=content,
                title=title or path.stem,
                source=str(file_path),
                source_type=source_type,
                business_id=business_id,
                metadata=metadata,
                db=db,
            )

        except Exception as e:
            logger.error("file_processing_error", error=str(e), file_path=file_path)
            raise

    def _extract_pdf(self, file_path: str) -> tuple[str, Optional[str]]:
        """
        Extract text from PDF
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Tuple of (content, title)
        """
        try:
            import PyPDF2

            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_parts = []
                title = None

                # Try to get title from metadata
                if pdf_reader.metadata and pdf_reader.metadata.title:
                    title = pdf_reader.metadata.title

                # Extract text from all pages
                for page in pdf_reader.pages:
                    text_parts.append(page.extract_text())

                content = "\n".join(text_parts)
                return content, title

        except Exception as e:
            logger.error("pdf_extraction_error", error=str(e), file_path=file_path)
            raise KnowledgeBaseError(f"Failed to extract PDF: {str(e)}") from e

    def _extract_docx(self, file_path: str) -> tuple[str, Optional[str]]:
        """
        Extract text from DOCX
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Tuple of (content, title)
        """
        try:
            from docx import Document

            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs]
            content = "\n".join(paragraphs)

            # Try to get title (usually first paragraph or core properties)
            title = None
            if doc.core_properties.title:
                title = doc.core_properties.title
            elif paragraphs:
                title = paragraphs[0] if len(paragraphs[0]) < 100 else None

            return content, title

        except Exception as e:
            logger.error("docx_extraction_error", error=str(e), file_path=file_path)
            raise KnowledgeBaseError(f"Failed to extract DOCX: {str(e)}") from e

    def _extract_txt(self, file_path: str) -> tuple[str, Optional[str]]:
        """
        Extract text from TXT file
        
        Args:
            file_path: Path to TXT file
            
        Returns:
            Tuple of (content, title)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            # Try to get title from first line
            lines = content.split("\n")
            title = lines[0].strip() if lines and len(lines[0]) < 100 else None

            return content, title

        except Exception as e:
            logger.error("txt_extraction_error", error=str(e), file_path=file_path)
            raise KnowledgeBaseError(f"Failed to extract TXT: {str(e)}") from e

    async def delete_document(
        self,
        vector_ids: List[str],
        business_id: Optional[str] = None,
        db: Optional[Any] = None,
    ) -> None:
        """
        Delete a document from knowledge base
        
        Args:
            vector_ids: List of vector IDs to delete
            business_id: Business configuration ID
            db: Database session
        """
        try:
            # Delete from vector store
            await self.vector_store.initialize()
            await self.vector_store.delete(ids=vector_ids, namespace=business_id)

            # Delete from database
            if db:
                db.query(KnowledgeEntry).filter(
                    KnowledgeEntry.vector_id.in_(vector_ids)
                ).delete(synchronize_session=False)
                db.commit()

            logger.info("document_deleted", vector_ids=len(vector_ids))

        except Exception as e:
            logger.error("document_deletion_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to delete document: {str(e)}") from e

