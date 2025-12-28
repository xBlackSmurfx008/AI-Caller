"""Documentation management API routes"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.api.schemas.documentation import (
    DocumentationSearch,
    DocumentationSearchResponse,
    DocumentationResult,
    VendorsResponse,
    VendorInfo,
    SyncStatus,
    DocumentationEntry,
    DocumentationFeedback,
)
from src.database.database import get_db
from src.database.models import KnowledgeEntry
from src.knowledge.rag_pipeline import RAGPipeline
from src.knowledge.documentation_scraper.factory import get_scraper_factory
from src.knowledge.document_processor import DocumentProcessor
from src.knowledge.documentation_scraper.sync_tracker import SyncTracker
from src.utils.errors import SyncError, DocumentationScrapingError
from src.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)

# Get scraper factory
scraper_factory = get_scraper_factory()


@router.get("/vendors", response_model=VendorsResponse)
async def get_vendors(
    db: Session = Depends(get_db),
):
    """Get list of available documentation vendors"""
    try:
        vendors = []
        
        for vendor_name in scraper_factory.get_all_vendors():
            scraper = scraper_factory.create_scraper(vendor_name)
            # Get document count
            count = db.query(func.count(KnowledgeEntry.id)).filter(
                KnowledgeEntry.vendor == vendor_name
            ).scalar() or 0
            
            # Get last synced time
            last_entry = db.query(KnowledgeEntry).filter(
                KnowledgeEntry.vendor == vendor_name
            ).order_by(KnowledgeEntry.last_synced.desc()).first()
            
            # Get doc types
            doc_types = db.query(KnowledgeEntry.doc_type).filter(
                KnowledgeEntry.vendor == vendor_name,
                KnowledgeEntry.doc_type.isnot(None)
            ).distinct().all()
            doc_types = [dt[0] for dt in doc_types if dt[0]]
            
            display_names = {
                "openai": "OpenAI",
                "twilio": "Twilio",
                "ringcentral": "RingCentral",
                "hubspot": "HubSpot",
                "google": "Google/Gemini",
            }
            
            vendors.append(VendorInfo(
                name=vendor_name,
                display_name=display_names.get(vendor_name, vendor_name.title()),
                base_url=scraper.base_url,
                last_synced=last_entry.last_synced if last_entry else None,
                document_count=count,
                doc_types=doc_types,
            ))
        
        return VendorsResponse(vendors=vendors)
    
    except Exception as e:
        logger.error("get_vendors_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get vendors: {str(e)}")


@router.post("/search", response_model=DocumentationSearchResponse)
async def search_documentation(
    search: DocumentationSearch,
    db: Session = Depends(get_db),
):
    """Search documentation"""
    try:
        # Initialize RAG pipeline
        rag = RAGPipeline(business_id=search.business_id)
        await rag.initialize()
        
        # Retrieve documents
        retrieved_docs = await rag.retrieve(
            query=search.query,
            top_k=search.top_k,
            vendor=search.vendor,
            doc_type=search.doc_type,
        )
        
        # Format results
        results = []
        vendors_seen = set()
        
        for doc in retrieved_docs:
            metadata = doc.get("metadata", {})
            vendor = metadata.get("vendor")
            if vendor:
                vendors_seen.add(vendor)
            
            results.append(DocumentationResult(
                id=doc.get("id", ""),
                title=metadata.get("title", "Unknown"),
                content=metadata.get("content", "")[:500],  # Truncate for response
                url=metadata.get("source", ""),
                vendor=vendor,
                doc_type=metadata.get("doc_type"),
                score=doc.get("score", 0.0),
                metadata=metadata,
            ))
        
        return DocumentationSearchResponse(
            query=search.query,
            results=results,
            total_results=len(results),
            vendors=list(vendors_seen),
        )
    
    except Exception as e:
        logger.error("documentation_search_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/sync/{vendor}")
async def sync_vendor_documentation(
    vendor: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger documentation sync for a vendor"""
    try:
        scraper_factory.create_scraper(vendor)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Vendor '{vendor}' not found")
    
    # Check for existing in-progress sync
    from src.database.models import SyncProgress
    existing = db.query(SyncProgress).filter(
        SyncProgress.vendor == vendor,
        SyncProgress.status == "in_progress"
    ).first()
    
    if existing:
        return {
            "status": "already_in_progress",
            "vendor": vendor,
            "message": f"Sync already in progress for {vendor}",
            "progress_id": existing.id,
        }
    
    # Add background task to sync documentation
    background_tasks.add_task(sync_documentation_task, vendor, db)
    
    return {
        "status": "started",
        "vendor": vendor,
        "message": f"Documentation sync started for {vendor}",
    }


@router.get("/sync/{vendor}/status", response_model=SyncStatus)
async def get_sync_status(
    vendor: str,
    db: Session = Depends(get_db),
):
    """Get sync status for a vendor"""
    from src.database.models import SyncProgress
    
    progress = db.query(SyncProgress).filter(
        SyncProgress.vendor == vendor
    ).order_by(SyncProgress.created_at.desc()).first()
    
    if not progress:
        raise HTTPException(status_code=404, detail=f"No sync found for vendor '{vendor}'")
    
    return SyncStatus(
        vendor=progress.vendor,
        status=progress.status,
        started_at=progress.started_at,
        completed_at=progress.completed_at,
        pages_scraped=progress.pages_scraped,
        pages_processed=progress.pages_processed,
        errors=[e.get("error", str(e)) for e in progress.errors[-10:]],  # Last 10 errors
    )


async def sync_documentation_task(vendor: str, db: Session):
    """Background task to sync documentation"""
    scraper = None
    tracker = None
    try:
        scraper = scraper_factory.create_scraper(vendor)
        processor = DocumentProcessor()
        tracker = SyncTracker(vendor, db)
        
        # Start or resume sync
        progress = tracker.start_sync()
        
        # Invalidate cache for this vendor when starting new sync
        if progress.status == "in_progress" and progress.pages_scraped == 0:
            await scraper._invalidate_cache()
        
        # Get start URLs
        start_urls = scraper.get_start_urls()
        visited_urls = set(progress.visited_urls)  # Resume from previous state
        urls_to_visit = [url for url in start_urls if url not in visited_urls]
        
        # Add any URLs that were in progress
        if progress.current_url and progress.current_url not in visited_urls:
            urls_to_visit.insert(0, progress.current_url)
        
        pages_scraped = progress.pages_scraped
        pages_processed = progress.pages_processed
        
        # Determine if we need Playwright (for JavaScript-heavy sites)
        use_playwright = vendor in ['openai', 'twilio', 'ringcentral', 'hubspot']
        
        # Scraping loop
        max_pages = 200  # Limit to prevent excessive scraping
        while urls_to_visit and pages_scraped < max_pages:
            url = urls_to_visit.pop(0)
            
            if url in visited_urls:
                continue
            
            visited_urls.add(url)
            tracker.update_progress(current_url=url, visited_url=url)
            
            try:
                logger.info("scraping_url", url=url, vendor=vendor)
                
                # Fetch HTML content
                html = await scraper.fetch_html(url, use_playwright=use_playwright)
                
                # Extract content and metadata
                content_data = await scraper.extract_content(html, url)
                
                # Skip if content is too short or empty
                if not content_data.get("content") or len(content_data["content"]) < 100:
                    logger.debug("skipping_short_content", url=url)
                    pages_scraped += 1
                    tracker.update_progress(pages_scraped=pages_scraped)
                    continue
                
                # Process and store document
                await processor.process_document(
                    content=content_data["content"],
                    title=content_data["title"],
                    source=url,
                    source_type="url",
                    vendor=vendor,
                    doc_type=content_data.get("doc_type"),
                    api_version=content_data.get("metadata", {}).get("api_version"),
                    endpoint=content_data.get("metadata", {}).get("endpoint"),
                    tags=content_data.get("metadata", {}).get("tags", []),
                    metadata=content_data.get("metadata", {}),
                    db=db,
                )
                
                pages_processed += 1
                pages_scraped += 1
                tracker.update_progress(
                    pages_scraped=pages_scraped,
                    pages_processed=pages_processed
                )
                
                # Extract links for further scraping
                links = scraper.extract_links(html, url)
                for link in links:
                    if link not in visited_urls and scraper.should_scrape(link):
                        urls_to_visit.append(link)
                
                # Log progress every 10 pages
                if pages_scraped % 10 == 0:
                    logger.info("sync_progress", vendor=vendor, pages=pages_scraped, processed=pages_processed)
                
            except DocumentationScrapingError as e:
                error_msg = f"{url}: {e.message}"
                logger.error(
                    "scraping_error",
                    url=url,
                    error=e.message,
                    error_code=e.code,
                    error_details=e.details,
                )
                tracker.add_error(error_msg, url=url)
                # Continue with next URL even if one fails
            except Exception as e:
                error_msg = f"{url}: {str(e)}"
                logger.error(
                    "scraping_error",
                    url=url,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,  # Include full traceback
                )
                tracker.add_error(error_msg, url=url)
                # Continue with next URL even if one fails
        
        # Mark sync as completed
        tracker.complete_sync()
        
        logger.info(
            "sync_completed",
            vendor=vendor,
            pages_scraped=pages_scraped,
            pages_processed=pages_processed,
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error(
            "sync_task_error",
            vendor=vendor,
            error=error_msg,
            error_type=type(e).__name__,
            exc_info=True,  # Include full traceback
        )
        if tracker:
            tracker.fail_sync(error_msg)
        raise SyncError(
            f"Documentation sync failed for {vendor}: {error_msg}",
            code="SYNC_ERROR",
            details={"vendor": vendor, "error": error_msg}
        ) from e
    finally:
        # Close HTTP client
        if scraper:
            await scraper.close()


@router.get("/{doc_id}", response_model=DocumentationEntry)
async def get_documentation_entry(
    doc_id: int,
    db: Session = Depends(get_db),
):
    """Get specific documentation entry"""
    entry = db.query(KnowledgeEntry).filter(KnowledgeEntry.id == doc_id).first()
    
    if not entry:
        raise HTTPException(status_code=404, detail="Documentation entry not found")
    
    return DocumentationEntry(
        id=entry.id,
        title=entry.title,
        url=entry.source or "",
        vendor=entry.vendor,
        doc_type=entry.doc_type,
        api_version=entry.api_version,
        endpoint=entry.endpoint,
        tags=entry.tags or [],
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        last_synced=entry.last_synced,
    )


@router.post("/feedback")
async def submit_feedback(
    feedback: DocumentationFeedback,
    db: Session = Depends(get_db),
):
    """Submit feedback on documentation relevance"""
    # Store feedback for analytics (implementation depends on requirements)
    logger.info(
        "documentation_feedback",
        doc_id=feedback.doc_id,
        query=feedback.query,
        relevant=feedback.relevant,
        comment=feedback.comment,
    )
    
    return {"status": "received", "message": "Feedback recorded"}

