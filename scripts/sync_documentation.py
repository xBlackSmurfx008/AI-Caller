#!/usr/bin/env python3
"""CLI tool for syncing vendor documentation"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Scrapers are now accessed via factory
from src.knowledge.document_processor import DocumentProcessor
from src.knowledge.documentation_scraper.sync_tracker import SyncTracker
from src.knowledge.documentation_scraper.factory import get_scraper_factory
from src.database.database import get_db
from src.utils.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

scraper_factory = get_scraper_factory()


async def sync_vendor(vendor: str, max_pages: int = 100):
    """Sync documentation for a vendor"""
    try:
        scraper = scraper_factory.create_scraper(vendor)
    except ValueError:
        logger.error("unknown_vendor", vendor=vendor)
        print(f"Unknown vendor: {vendor}")
        print(f"Available vendors: {', '.join(scraper_factory.get_all_vendors())}")
        return
    
    processor = DocumentProcessor()
    
    # Get database session
    db = next(get_db())
    tracker = SyncTracker(vendor, db)
    
    try:
        # Start or resume sync
        progress = tracker.start_sync()
        
        # Invalidate cache for this vendor when starting new sync
        if progress.status == "in_progress" and progress.pages_scraped == 0:
            await scraper._invalidate_cache()
        
        logger.info("sync_started", vendor=vendor)
        print(f"Starting sync for {vendor}...")
        
        # Get start URLs
        start_urls = scraper.get_start_urls()
        visited_urls = set(progress.visited_urls)
        urls_to_visit = [url for url in start_urls if url not in visited_urls]
        
        # Add any URLs that were in progress
        if progress.current_url and progress.current_url not in visited_urls:
            urls_to_visit.insert(0, progress.current_url)
        
        pages_scraped = progress.pages_scraped
        pages_processed = progress.pages_processed
        
        # Determine if we need Playwright
        use_playwright = vendor in ['openai', 'twilio', 'ringcentral', 'hubspot']
        
        while urls_to_visit and pages_scraped < max_pages:
            url = urls_to_visit.pop(0)
            
            if url in visited_urls:
                continue
            
            visited_urls.add(url)
            tracker.update_progress(current_url=url, visited_url=url)
            
            try:
                logger.info("scraping_url", url=url, vendor=vendor)
                print(f"  Scraping: {url}")
                
                # Fetch HTML content
                html = await scraper.fetch_html(url, use_playwright=use_playwright)
                
                # Extract content and metadata
                content_data = await scraper.extract_content(html, url)
                
                # Skip if content is too short
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
                print(f"    ✓ Processed: {content_data['title'][:50]}")
                
                # Extract links for further scraping
                links = scraper.extract_links(html, url)
                for link in links:
                    if link not in visited_urls and scraper.should_scrape(link):
                        urls_to_visit.append(link)
                
            except Exception as e:
                error_msg = f"{url}: {str(e)}"
                logger.error(
                    "scraping_error",
                    url=url,
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True,
                )
                tracker.add_error(error_msg, url=url)
                print(f"    ✗ Error: {str(e)}")
        
        # Mark sync as completed
        tracker.complete_sync()
        
        logger.info("sync_completed", vendor=vendor, pages=pages_processed)
        print(f"\nSync completed for {vendor}")
        print(f"  Pages processed: {pages_processed}")
        
        progress_info = tracker.get_progress()
        if progress_info and progress_info.get("error_count", 0) > 0:
            print(f"  Errors: {progress_info['error_count']}")
    
    except Exception as e:
        logger.error(
            "sync_task_error",
            vendor=vendor,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        if tracker:
            tracker.fail_sync(str(e))
        raise
    finally:
        # Close HTTP client
        if scraper:
            await scraper.close()
        db.close()


async def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python sync_documentation.py <vendor> [max_pages]")
        print(f"Available vendors: {', '.join(SCRAPERS.keys())}")
        print("Example: python sync_documentation.py openai 50")
        sys.exit(1)
    
    vendor = sys.argv[1].lower()
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    
    await sync_vendor(vendor, max_pages)


if __name__ == "__main__":
    asyncio.run(main())

