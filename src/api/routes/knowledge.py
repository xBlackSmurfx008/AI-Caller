"""Knowledge base management routes"""

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from src.database.database import get_db
from src.services.knowledge_service import KnowledgeService
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
from src.api.utils import handle_service_errors, handle_service_errors_sync

router = APIRouter()


def get_knowledge_service() -> KnowledgeService:
    """Dependency to get knowledge service instance"""
    return KnowledgeService()


@router.post("/documents", response_model=DocumentResponse)
@handle_service_errors
async def upload_document(
    document: DocumentUpload,
    db: Session = Depends(get_db),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """Upload a document to the knowledge base"""
    return await service.upload_document(document, db)


@router.post("/documents/bulk", response_model=BulkUploadResponse)
@handle_service_errors
async def bulk_upload_documents(
    request: BulkUploadRequest,
    db: Session = Depends(get_db),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """Bulk upload documents"""
    return await service.bulk_upload_documents(request, db)


@router.get("/documents", response_model=List[DocumentResponse])
@handle_service_errors_sync
def list_documents(
    business_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """List all documents in knowledge base"""
    return service.list_documents(db, business_id, skip, limit)


@router.get("/documents/{document_id}", response_model=DocumentResponse)
@handle_service_errors_sync
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """Get a specific document"""
    return service.get_document(document_id, db)


@router.delete("/documents/{document_id}")
@handle_service_errors
async def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """Delete a document from knowledge base"""
    await service.delete_document(document_id, db)
    return {"message": "Document deleted successfully", "document_id": document_id}


@router.post("/search", response_model=SearchResponse)
@handle_service_errors
async def search_documents(
    search: DocumentSearch,
    db: Session = Depends(get_db),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """Search documents in knowledge base"""
    return await service.search_documents(search, db)


@router.post("/feedback")
@handle_service_errors_sync
def submit_feedback(
    feedback: FeedbackRequest,
    db: Session = Depends(get_db),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """Submit feedback on search results"""
    service.submit_feedback(feedback, db)
    return {"message": "Feedback recorded successfully"}


@router.get("/analytics", response_model=AnalyticsResponse)
@handle_service_errors_sync
def get_analytics(
    db: Session = Depends(get_db),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """Get knowledge base analytics"""
    return service.get_analytics(db)


# Frontend-compatible routes (aliases for backward compatibility)
@router.get("/")
@handle_service_errors_sync
def list_knowledge_entries(
    business_id: Optional[str] = None,
    page: int = 1,
    limit: int = 100,
    db: Session = Depends(get_db),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """List all knowledge entries (frontend-compatible endpoint)"""
    skip = (page - 1) * limit if page > 0 else 0
    entries = service.list_documents(db, business_id, skip, limit)
    
    # Convert to frontend-expected format
    return {
        "entries": entries,
        "pagination": {
            "page": page,
            "limit": limit,
            "total": len(entries),  # Note: This is approximate, full count would require a separate query
            "total_pages": (len(entries) + limit - 1) // limit if limit > 0 else 1,
        }
    }


@router.post("/")
@handle_service_errors
async def create_knowledge_entry(
    document: DocumentUpload,
    db: Session = Depends(get_db),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """Create a knowledge entry (frontend-compatible endpoint)"""
    entry = await service.upload_document(document, db)
    return {"entry": entry, "message": "Entry created successfully"}


@router.post("/upload")
@handle_service_errors
async def upload_file(
    file: UploadFile = File(...),
    business_id: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """Upload a file to knowledge base (frontend-compatible endpoint)"""
    # Read file content
    content = await file.read()
    content_str = content.decode('utf-8', errors='ignore')
    
    document = DocumentUpload(
        title=title or file.filename or "Uploaded Document",
        content=content_str,
        source=file.filename,
        source_type=file.content_type or "text",
        business_id=business_id,
    )
    entry = await service.upload_document(document, db)
    return {"entry": entry, "processing_status": "completed"}


@router.delete("/{entry_id}")
@handle_service_errors
async def delete_knowledge_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    service: KnowledgeService = Depends(get_knowledge_service),
):
    """Delete a knowledge entry (frontend-compatible endpoint)"""
    await service.delete_document(entry_id, db)
    return {"message": "Entry deleted successfully", "entry_id": entry_id}

