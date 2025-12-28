"""Knowledge base service layer"""

from typing import List, Optional
from sqlalchemy.orm import Session

from src.database.models import KnowledgeEntry
from src.knowledge.document_processor import DocumentProcessor
from src.knowledge.hybrid_search import HybridSearch
from src.knowledge.feedback_handler import FeedbackHandler, FeedbackType
from src.knowledge.analytics import KnowledgeBaseAnalytics
from src.api.schemas.knowledge import (
    DocumentUpload,
    DocumentResponse,
    DocumentSearch,
    SearchResponse,
    FeedbackRequest,
    BulkUploadRequest,
    BulkUploadResponse,
    AnalyticsResponse,
)
from src.utils.logging import get_logger
from src.utils.errors import KnowledgeBaseError, NotFoundError

logger = get_logger(__name__)


class KnowledgeService:
    """Service for knowledge base operations"""

    def __init__(
        self,
        document_processor: Optional[DocumentProcessor] = None,
        feedback_handler: Optional[FeedbackHandler] = None,
        analytics: Optional[KnowledgeBaseAnalytics] = None,
    ):
        """Initialize knowledge service with dependencies"""
        self.document_processor = document_processor or DocumentProcessor()
        self.feedback_handler = feedback_handler or FeedbackHandler()
        self.analytics = analytics or KnowledgeBaseAnalytics()

    async def upload_document(
        self,
        document: DocumentUpload,
        db: Session,
    ) -> DocumentResponse:
        """Upload a document to the knowledge base"""
        if not document.content and not document.source:
            raise ValueError("Either content or source must be provided")

        try:
            # Process document
            if document.content:
                vector_ids = await self.document_processor.process_document(
                    content=document.content,
                    title=document.title or "Untitled",
                    source=document.source,
                    source_type=document.source_type or "text",
                    business_id=document.business_id,
                    metadata=document.metadata,
                    db=db,
                )
            else:
                vector_ids = await self.document_processor.process_file(
                    file_path=document.source,
                    business_id=document.business_id,
                    metadata=document.metadata,
                    db=db,
                )

            # Get created entry
            entry = db.query(KnowledgeEntry).filter(
                KnowledgeEntry.vector_id == vector_ids[0]
            ).first()

            if not entry:
                raise KnowledgeBaseError("Failed to create document entry")

            return self._entry_to_response(entry)

        except Exception as e:
            logger.error("document_upload_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to upload document: {str(e)}")

    async def bulk_upload_documents(
        self,
        request: BulkUploadRequest,
        db: Session,
    ) -> BulkUploadResponse:
        """Bulk upload documents"""
        successful = 0
        failed = 0
        document_ids = []

        for doc in request.documents:
            try:
                if doc.content:
                    vector_ids = await self.document_processor.process_document(
                        content=doc.content,
                        title=doc.title or "Untitled",
                        source=doc.source,
                        source_type=doc.source_type or "text",
                        business_id=doc.business_id or request.business_id,
                        metadata=doc.metadata,
                        db=db,
                    )
                else:
                    vector_ids = await self.document_processor.process_file(
                        file_path=doc.source,
                        business_id=doc.business_id or request.business_id,
                        metadata=doc.metadata,
                        db=db,
                    )

                entry = db.query(KnowledgeEntry).filter(
                    KnowledgeEntry.vector_id == vector_ids[0]
                ).first()

                if entry:
                    document_ids.append(entry.id)
                    successful += 1
                else:
                    failed += 1

            except Exception as e:
                logger.error("bulk_upload_item_error", error=str(e))
                failed += 1

        return BulkUploadResponse(
            total=len(request.documents),
            successful=successful,
            failed=failed,
            document_ids=document_ids,
        )

    def list_documents(
        self,
        db: Session,
        business_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DocumentResponse]:
        """List all documents in knowledge base"""
        query = db.query(KnowledgeEntry)

        if business_id:
            query = query.filter(KnowledgeEntry.business_id == business_id)

        entries = query.offset(skip).limit(limit).all()

        return [self._entry_to_response(entry) for entry in entries]

    def get_document(
        self,
        document_id: int,
        db: Session,
    ) -> DocumentResponse:
        """Get a specific document"""
        entry = db.query(KnowledgeEntry).filter(
            KnowledgeEntry.id == document_id
        ).first()

        if not entry:
            raise NotFoundError("Document not found")

        return self._entry_to_response(entry)

    async def delete_document(
        self,
        document_id: int,
        db: Session,
    ) -> None:
        """Delete a document from knowledge base"""
        entry = db.query(KnowledgeEntry).filter(
            KnowledgeEntry.id == document_id
        ).first()

        if not entry:
            raise NotFoundError("Document not found")

        try:
            await self.document_processor.delete_document(
                vector_ids=[entry.vector_id] if entry.vector_id else [],
                business_id=entry.business_id,
                db=db,
            )
        except Exception as e:
            logger.error("document_deletion_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to delete document: {str(e)}")

    async def search_documents(
        self,
        search: DocumentSearch,
        db: Session,
    ) -> SearchResponse:
        """Search documents in knowledge base"""
        try:
            hybrid_search = HybridSearch()

            # Perform search
            results = await hybrid_search.search(
                query=search.query,
                top_k=search.top_k,
                namespace=search.business_id,
                metadata_filter=search.metadata_filter,
            )

            # Format results
            formatted_results = []
            citations = []

            for i, result in enumerate(results):
                metadata = result.get("metadata", {})
                formatted_results.append({
                    "id": result.get("id"),
                    "title": metadata.get("title", "Unknown"),
                    "content": metadata.get("content", "")[:500],  # Truncate for response
                    "source": metadata.get("source"),
                    "score": result.get("score", 0.0),
                    "metadata": metadata,
                })

                citations.append({
                    "id": f"[{i+1}]",
                    "title": metadata.get("title", "Unknown"),
                    "source": metadata.get("source"),
                    "score": result.get("score", 0.0),
                })

            # Track query for analytics
            self.analytics.track_query(search.query, results)

            return SearchResponse(
                query=search.query,
                results=formatted_results,
                total_results=len(formatted_results),
                citations=citations,
            )

        except Exception as e:
            logger.error("search_error", error=str(e))
            raise KnowledgeBaseError(f"Search failed: {str(e)}")

    def submit_feedback(
        self,
        feedback: FeedbackRequest,
        db: Session,
    ) -> None:
        """Submit feedback on search results"""
        try:
            feedback_type = FeedbackType(feedback.feedback_type)

            self.feedback_handler.record_feedback(
                query=feedback.query,
                result_id=feedback.result_id,
                feedback_type=feedback_type,
                rating=feedback.rating,
                correction=feedback.correction,
                db=db,
            )
        except Exception as e:
            logger.error("feedback_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to record feedback: {str(e)}")

    def get_analytics(
        self,
        db: Session,
    ) -> AnalyticsResponse:
        """Get knowledge base analytics"""
        try:
            dashboard_data = self.analytics.get_analytics_dashboard_data(db=db)

            return AnalyticsResponse(
                total_documents=dashboard_data.get("total_documents", 0),
                total_queries=dashboard_data.get("total_queries", 0),
                average_accuracy=dashboard_data.get("average_accuracy", 0.0),
                knowledge_gaps=dashboard_data.get("knowledge_gaps", []),
                top_queries=dashboard_data.get("top_queries", []),
            )
        except Exception as e:
            logger.error("analytics_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to get analytics: {str(e)}")

    def _entry_to_response(self, entry: KnowledgeEntry) -> DocumentResponse:
        """Convert KnowledgeEntry model to DocumentResponse schema"""
        return DocumentResponse(
            id=entry.id,
            title=entry.title,
            content=entry.content,
            source=entry.source,
            source_type=entry.source_type,
            business_id=entry.business_id,
            vector_id=entry.vector_id,
            created_at=entry.created_at.isoformat(),
            updated_at=entry.updated_at.isoformat(),
            metadata=entry.meta_data or {},
        )

