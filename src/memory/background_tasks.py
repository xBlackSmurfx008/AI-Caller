"""Background task processing for memory summaries"""

import asyncio
import threading
from typing import Optional
from sqlalchemy.orm import Session
from queue import Queue, Empty
from datetime import datetime

from src.memory.memory_service import MemoryService
from src.database.database import SessionLocal
from src.utils.logging import get_logger

logger = get_logger(__name__)
memory_service = MemoryService()

# Task queue for background processing
_summary_queue: Queue = Queue()
_worker_thread: Optional[threading.Thread] = None
_worker_running = False


def queue_summary_generation(interaction_id: str, contact_id: str, contact_name: Optional[str] = None) -> None:
    """
    Queue a summary generation task to be processed in the background
    
    Args:
        interaction_id: Interaction ID to summarize
        contact_id: Contact ID
        contact_name: Optional contact name
    """
    task = {
        "interaction_id": interaction_id,
        "contact_id": contact_id,
        "contact_name": contact_name,
        "queued_at": datetime.utcnow().isoformat()
    }
    _summary_queue.put(task)
    logger.info("summary_queued", interaction_id=interaction_id, queue_size=_summary_queue.qsize())


def _process_summary_queue() -> None:
    """Background worker that processes summary generation tasks"""
    global _worker_running
    
    logger.info("summary_worker_started")
    _worker_running = True
    
    while _worker_running:
        try:
            # Get task from queue (blocking with timeout)
            try:
                task = _summary_queue.get(timeout=1)
            except Empty:
                continue
            
            interaction_id = task["interaction_id"]
            contact_id = task["contact_id"]
            contact_name = task.get("contact_name")
            
            # Create new database session for this task
            db = SessionLocal()
            
            try:
                logger.info("processing_summary", interaction_id=interaction_id)
                
                # Generate summary
                memory_service.generate_summary(
                    db=db,
                    interaction_id=interaction_id,
                    contact_name=contact_name
                )
                
                logger.info("summary_generated_background", interaction_id=interaction_id)
                
            except Exception as e:
                logger.error(
                    "background_summary_generation_failed",
                    error=str(e),
                    interaction_id=interaction_id
                )
            finally:
                db.close()
                _summary_queue.task_done()
                
        except Exception as e:
            logger.error("summary_worker_error", error=str(e))
    
    logger.info("summary_worker_stopped")


def start_background_worker() -> None:
    """Start the background worker thread"""
    global _worker_thread, _worker_running
    
    if _worker_thread and _worker_thread.is_alive():
        logger.warning("summary_worker_already_running")
        return
    
    _worker_thread = threading.Thread(
        target=_process_summary_queue,
        daemon=True,
        name="MemorySummaryWorker"
    )
    _worker_thread.start()
    logger.info("background_worker_started")


def stop_background_worker() -> None:
    """Stop the background worker thread"""
    global _worker_running
    
    _worker_running = False
    if _worker_thread:
        _worker_thread.join(timeout=5)
    logger.info("background_worker_stopped")


def get_queue_size() -> int:
    """Get current queue size"""
    return _summary_queue.qsize()

