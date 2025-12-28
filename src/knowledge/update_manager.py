"""Automatic knowledge update manager with versioning"""

import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path

from sqlalchemy.orm import Session

from src.database.database import get_db
from src.database.models import KnowledgeEntry
from src.knowledge.document_processor import DocumentProcessor
from src.utils.logging import get_logger

logger = get_logger(__name__)


class UpdateManager:
    """Manage document updates and versioning"""

    def __init__(self):
        """Initialize update manager"""
        self.document_processor = DocumentProcessor()

    def detect_changes(
        self,
        file_path: str,
        existing_entry: Optional[KnowledgeEntry] = None,
    ) -> Dict[str, Any]:
        """
        Detect changes in document
        
        Args:
            file_path: Path to document
            existing_entry: Existing knowledge entry
            
        Returns:
            Change detection results
        """
        path = Path(file_path)
        
        if not path.exists():
            return {
                "has_changes": False,
                "change_type": "deleted",
            }
        
        # Calculate file hash
        current_hash = self._calculate_file_hash(file_path)
        
        if existing_entry:
            existing_hash = existing_entry.meta_data.get("file_hash")
            
            if existing_hash != current_hash:
                return {
                    "has_changes": True,
                    "change_type": "modified",
                    "old_hash": existing_hash,
                    "new_hash": current_hash,
                }
        else:
            return {
                "has_changes": True,
                "change_type": "new",
                "file_hash": current_hash,
            }
        
        return {
            "has_changes": False,
            "change_type": "unchanged",
        }

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate file hash"""
        hash_obj = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    async def incremental_reindex(
        self,
        file_path: str,
        business_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> List[str]:
        """
        Incrementally reindex updated document
        
        Args:
            file_path: Path to document
            business_id: Business ID
            db: Database session
            
        Returns:
            List of new vector IDs
        """
        if db is None:
            db = next(get_db())
        
        try:
            # Find existing entry
            source = str(file_path)
            existing = db.query(KnowledgeEntry).filter(
                KnowledgeEntry.source == source,
                KnowledgeEntry.business_id == business_id,
            ).first()
            
            # Delete old vectors if exists
            if existing and existing.vector_id:
                # Get all vector IDs for this document
                # Note: This assumes vector_id stores reference to first chunk
                # In production, you'd track all vector IDs
                try:
                    await self.document_processor.delete_document(
                        vector_ids=[existing.vector_id],
                        business_id=business_id,
                        db=db,
                    )
                except Exception as e:
                    logger.warning("vector_deletion_warning", error=str(e))
            
            # Process updated document
            vector_ids = await self.document_processor.process_file(
                file_path=file_path,
                business_id=business_id,
                db=db,
            )
            
            # Update metadata with version info
            if existing:
                existing.updated_at = datetime.utcnow()
                existing.meta_data["version"] = existing.meta_data.get("version", 0) + 1
                existing.meta_data["file_hash"] = self._calculate_file_hash(file_path)
                db.commit()
            
            return vector_ids
            
        except Exception as e:
            logger.error("incremental_reindex_error", error=str(e), file_path=file_path)
            raise

    def handle_document_deletion(
        self,
        document_id: int,
        business_id: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> None:
        """
        Handle document deletion gracefully
        
        Args:
            document_id: Document ID
            business_id: Business ID
            db: Database session
        """
        if db is None:
            db = next(get_db())
        
        try:
            entry = db.query(KnowledgeEntry).filter(
                KnowledgeEntry.id == document_id,
                KnowledgeEntry.business_id == business_id,
            ).first()
            
            if entry:
                # Delete vectors
                if entry.vector_id:
                    await self.document_processor.delete_document(
                        vector_ids=[entry.vector_id],
                        business_id=business_id,
                        db=db,
                    )
                
                # Delete database entry
                db.delete(entry)
                db.commit()
                
                logger.info("document_deleted", document_id=document_id)
            
        except Exception as e:
            logger.error("document_deletion_error", error=str(e), document_id=document_id)
            raise

    def detect_stale_content(
        self,
        max_age_days: int = 365,
        db: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """
        Detect stale content
        
        Args:
            max_age_days: Maximum age in days
            db: Database session
            
        Returns:
            List of stale documents
        """
        if db is None:
            db = next(get_db())
        
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)
        
        stale = db.query(KnowledgeEntry).filter(
            KnowledgeEntry.updated_at < cutoff_date
        ).all()
        
        return [
            {
                "id": entry.id,
                "title": entry.title,
                "source": entry.source,
                "last_updated": entry.updated_at.isoformat(),
                "age_days": (datetime.utcnow() - entry.updated_at).days,
            }
            for entry in stale
        ]

    def version_document(
        self,
        document_id: int,
        db: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Get document version information
        
        Args:
            document_id: Document ID
            db: Database session
            
        Returns:
            Version information
        """
        if db is None:
            db = next(get_db())
        
        entry = db.query(KnowledgeEntry).filter(
            KnowledgeEntry.id == document_id
        ).first()
        
        if not entry:
            return {}
        
        return {
            "id": entry.id,
            "version": entry.meta_data.get("version", 1),
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat(),
            "file_hash": entry.meta_data.get("file_hash"),
        }

