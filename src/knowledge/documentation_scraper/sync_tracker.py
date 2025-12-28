"""Progress tracking for documentation synchronization"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from src.database.models import SyncProgress
from src.utils.logging import get_logger

logger = get_logger(__name__)


class SyncTracker:
    """Track and manage documentation sync progress"""
    
    def __init__(self, vendor: str, db: Session):
        """
        Initialize sync tracker
        
        Args:
            vendor: Vendor name
            db: Database session
        """
        self.vendor = vendor
        self.db = db
        self.progress: Optional[SyncProgress] = None
    
    def start_sync(self, total_pages: Optional[int] = None) -> SyncProgress:
        """
        Start a new sync or resume existing one
        
        Args:
            total_pages: Optional total number of pages expected
            
        Returns:
            SyncProgress instance
        """
        # Check for existing in-progress sync
        existing = self.db.query(SyncProgress).filter(
            SyncProgress.vendor == self.vendor,
            SyncProgress.status == "in_progress"
        ).first()
        
        if existing:
            logger.info("resuming_sync", vendor=self.vendor, progress_id=existing.id)
            self.progress = existing
            return existing
        
        # Create new sync progress
        self.progress = SyncProgress(
            vendor=self.vendor,
            status="in_progress",
            started_at=datetime.utcnow(),
            total_pages=total_pages,
            pages_scraped=0,
            pages_processed=0,
            visited_urls=[],
            errors=[],
        )
        self.db.add(self.progress)
        self.db.commit()
        self.db.refresh(self.progress)
        
        logger.info("sync_started", vendor=self.vendor, progress_id=self.progress.id)
        return self.progress
    
    def update_progress(
        self,
        pages_scraped: Optional[int] = None,
        pages_processed: Optional[int] = None,
        current_url: Optional[str] = None,
        visited_url: Optional[str] = None,
    ) -> None:
        """
        Update sync progress
        
        Args:
            pages_scraped: Number of pages scraped
            pages_processed: Number of pages processed
            current_url: Current URL being processed
            visited_url: URL that was just visited
        """
        if not self.progress:
            logger.warning("no_progress_to_update", vendor=self.vendor)
            return
        
        if pages_scraped is not None:
            self.progress.pages_scraped = pages_scraped
        if pages_processed is not None:
            self.progress.pages_processed = pages_processed
        if current_url is not None:
            self.progress.current_url = current_url
        if visited_url is not None:
            if visited_url not in self.progress.visited_urls:
                self.progress.visited_urls.append(visited_url)
        
        self.progress.updated_at = datetime.utcnow()
        self.db.commit()
    
    def add_error(self, error: str, url: Optional[str] = None) -> None:
        """
        Add error to progress tracking
        
        Args:
            error: Error message
            url: Optional URL where error occurred
        """
        if not self.progress:
            logger.warning("no_progress_to_update", vendor=self.vendor)
            return
        
        error_entry = {
            "error": error,
            "url": url,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.progress.errors.append(error_entry)
        self.progress.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.warning("sync_error", vendor=self.vendor, error=error, url=url)
    
    def complete_sync(self) -> None:
        """Mark sync as completed"""
        if not self.progress:
            logger.warning("no_progress_to_complete", vendor=self.vendor)
            return
        
        self.progress.status = "completed"
        self.progress.completed_at = datetime.utcnow()
        self.progress.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info(
            "sync_completed",
            vendor=self.vendor,
            progress_id=self.progress.id,
            pages_scraped=self.progress.pages_scraped,
            pages_processed=self.progress.pages_processed,
        )
    
    def fail_sync(self, error: Optional[str] = None) -> None:
        """
        Mark sync as failed
        
        Args:
            error: Optional error message
        """
        if not self.progress:
            logger.warning("no_progress_to_fail", vendor=self.vendor)
            return
        
        self.progress.status = "failed"
        self.progress.completed_at = datetime.utcnow()
        if error:
            self.add_error(error)
        self.progress.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.error("sync_failed", vendor=self.vendor, progress_id=self.progress.id, error=error)
    
    def cancel_sync(self) -> None:
        """Cancel sync"""
        if not self.progress:
            logger.warning("no_progress_to_cancel", vendor=self.vendor)
            return
        
        self.progress.status = "cancelled"
        self.progress.completed_at = datetime.utcnow()
        self.progress.updated_at = datetime.utcnow()
        self.db.commit()
        
        logger.info("sync_cancelled", vendor=self.vendor, progress_id=self.progress.id)
    
    def get_progress(self) -> Optional[Dict[str, Any]]:
        """
        Get current progress as dictionary
        
        Returns:
            Progress dictionary or None
        """
        if not self.progress:
            return None
        
        return {
            "id": self.progress.id,
            "vendor": self.progress.vendor,
            "status": self.progress.status,
            "started_at": self.progress.started_at.isoformat() if self.progress.started_at else None,
            "completed_at": self.progress.completed_at.isoformat() if self.progress.completed_at else None,
            "pages_scraped": self.progress.pages_scraped,
            "pages_processed": self.progress.pages_processed,
            "total_pages": self.progress.total_pages,
            "current_url": self.progress.current_url,
            "visited_count": len(self.progress.visited_urls),
            "error_count": len(self.progress.errors),
            "progress_percentage": (
                (self.progress.pages_processed / self.progress.total_pages * 100)
                if self.progress.total_pages and self.progress.total_pages > 0
                else None
            ),
        }

