"""Schemas for documentation management"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentationSearch(BaseModel):
    """Documentation search request"""
    query: str = Field(..., description="Search query")
    vendor: Optional[str] = Field(None, description="Filter by vendor (openai, twilio, etc.)")
    doc_type: Optional[str] = Field(None, description="Filter by document type")
    top_k: int = Field(5, ge=1, le=20, description="Number of results")
    business_id: Optional[str] = Field(None, description="Business ID for namespace")


class DocumentationResult(BaseModel):
    """Documentation search result"""
    id: str
    title: str
    content: str
    url: str
    vendor: Optional[str] = None
    doc_type: Optional[str] = None
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentationSearchResponse(BaseModel):
    """Documentation search response"""
    query: str
    results: List[DocumentationResult]
    total_results: int
    vendors: List[str] = Field(default_factory=list)


class VendorInfo(BaseModel):
    """Vendor information"""
    name: str
    display_name: str
    base_url: str
    last_synced: Optional[datetime] = None
    document_count: int = 0
    doc_types: List[str] = Field(default_factory=list)


class VendorsResponse(BaseModel):
    """List of vendors response"""
    vendors: List[VendorInfo]


class SyncStatus(BaseModel):
    """Documentation sync status"""
    vendor: str
    status: str  # pending, in_progress, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    pages_scraped: int = 0
    pages_processed: int = 0
    errors: List[str] = Field(default_factory=list)


class DocumentationEntry(BaseModel):
    """Documentation entry details"""
    id: int
    title: str
    url: str
    vendor: Optional[str] = None
    doc_type: Optional[str] = None
    api_version: Optional[str] = None
    endpoint: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    last_synced: Optional[datetime] = None


class DocumentationFeedback(BaseModel):
    """Feedback on documentation relevance"""
    doc_id: str
    query: str
    relevant: bool
    comment: Optional[str] = None

