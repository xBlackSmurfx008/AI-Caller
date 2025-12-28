"""Pydantic schemas for knowledge base API"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DocumentUpload(BaseModel):
    """Schema for document upload"""
    title: Optional[str] = None
    content: Optional[str] = None
    source: Optional[str] = None
    source_type: Optional[str] = None
    business_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DocumentResponse(BaseModel):
    """Schema for document response"""
    id: int
    title: str
    content: str
    source: Optional[str] = None
    source_type: Optional[str] = None
    business_id: Optional[str] = None
    vector_id: Optional[str] = None
    created_at: str
    updated_at: str
    metadata: Dict[str, Any] = {}


class DocumentSearch(BaseModel):
    """Schema for document search"""
    query: str
    top_k: Optional[int] = Field(default=10, ge=1, le=50)
    business_id: Optional[str] = None
    metadata_filter: Optional[Dict[str, Any]] = None
    use_hybrid_search: bool = True
    use_reranking: bool = True


class SearchResult(BaseModel):
    """Schema for search result"""
    id: str
    title: str
    content: str
    source: Optional[str] = None
    score: float
    metadata: Dict[str, Any] = {}


class SearchResponse(BaseModel):
    """Schema for search response"""
    query: str
    results: List[SearchResult]
    total_results: int
    citations: List[Dict[str, Any]] = []


class FeedbackRequest(BaseModel):
    """Schema for feedback request"""
    query: str
    result_id: str
    feedback_type: str
    rating: Optional[int] = Field(None, ge=1, le=5)
    correction: Optional[str] = None


class BulkUploadRequest(BaseModel):
    """Schema for bulk upload"""
    documents: List[DocumentUpload]
    business_id: Optional[str] = None


class BulkUploadResponse(BaseModel):
    """Schema for bulk upload response"""
    total: int
    successful: int
    failed: int
    document_ids: List[int] = []


class AnalyticsResponse(BaseModel):
    """Schema for analytics response"""
    total_documents: int
    total_queries: int
    average_accuracy: float
    knowledge_gaps: List[Dict[str, Any]] = []
    top_queries: List[Dict[str, Any]] = []

