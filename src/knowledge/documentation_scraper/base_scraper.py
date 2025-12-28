"""Base scraper interface for documentation sources"""

import hashlib
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify as md

from src.knowledge.documentation_scraper.retry import retry_with_backoff
from src.utils.config import get_settings
from src.utils.errors import DocumentationScrapingError
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class BaseScraper(ABC):
    """Abstract base class for documentation scrapers"""

    def __init__(self, vendor: str, base_url: str, rate_limit_delay: float = 1.0):
        """
        Initialize base scraper
        
        Args:
            vendor: Vendor name (openai, twilio, etc.)
            base_url: Base URL for documentation
            rate_limit_delay: Delay between requests in seconds
        """
        self.vendor = vendor
        self.base_url = base_url
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0.0
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )

    def _rate_limit(self) -> None:
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()

    @abstractmethod
    def get_start_urls(self) -> List[str]:
        """
        Get list of starting URLs to scrape
        
        Returns:
            List of URLs to start scraping from
        """
        pass

    @abstractmethod
    def extract_links(self, html: str, current_url: str) -> List[str]:
        """
        Extract links to follow from HTML
        
        Args:
            html: HTML content
            current_url: Current page URL
            
        Returns:
            List of URLs to follow
        """
        pass

    @abstractmethod
    async def extract_content(self, html: str, url: str) -> Dict[str, Any]:
        """
        Extract content and metadata from HTML
        
        Args:
            html: HTML content
            url: Page URL
            
        Returns:
            Dictionary with title, content, metadata
        """
        pass

    def normalize_url(self, url: str, base_url: Optional[str] = None) -> str:
        """
        Normalize URL (remove fragments, query params if needed)
        
        Args:
            url: URL to normalize
            base_url: Optional base URL for relative URLs
            
        Returns:
            Normalized URL
        """
        if base_url:
            url = urljoin(base_url, url)
        
        parsed = urlparse(url)
        # Remove fragment
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        
        return normalized

    def html_to_markdown(self, html: str) -> str:
        """
        Convert HTML to Markdown
        
        Args:
            html: HTML content
            
        Returns:
            Markdown content
        """
        try:
            # Parse HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Convert to markdown
            markdown = md(str(soup), heading_style="ATX")
            return markdown.strip()
        
        except Exception as e:
            logger.error("html_to_markdown_error", error=str(e))
            # Fallback: extract text only
            soup = BeautifulSoup(html, 'html.parser')
            return soup.get_text(separator="\n").strip()

    def extract_code_blocks(self, html: str) -> List[Dict[str, str]]:
        """
        Extract code blocks from HTML
        
        Args:
            html: HTML content
            
        Returns:
            List of code blocks with language and code
        """
        soup = BeautifulSoup(html, 'html.parser')
        code_blocks = []
        
        # Find <pre><code> blocks
        for pre in soup.find_all('pre'):
            code = pre.find('code')
            if code:
                language = code.get('class', [])
                language = language[0].replace('language-', '') if language else 'text'
                code_text = code.get_text()
                code_blocks.append({
                    "language": language,
                    "code": code_text,
                })
        
        return code_blocks

    def generate_doc_id(self, url: str) -> str:
        """
        Generate unique document ID from URL
        
        Args:
            url: Document URL
            
        Returns:
            Unique document ID
        """
        return hashlib.md5(url.encode()).hexdigest()


    async def _fetch_html_internal(self, url: str, use_playwright: bool = False) -> str:
        """
        Internal method to fetch HTML (with retry logic applied via decorator)
        
        Args:
            url: URL to fetch
            use_playwright: Whether to use Playwright for JavaScript-rendered pages
            
        Returns:
            HTML content as string
        """
        if use_playwright:
            # Use Playwright for JavaScript-rendered pages
            try:
                from playwright.async_api import async_playwright
                
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    await page.goto(url, wait_until='networkidle', timeout=30000)
                    html = await page.content()
                    await browser.close()
                    return html
            except ImportError:
                logger.warning("playwright_not_installed", url=url)
                # Fallback to httpx
                pass
        
        # Use httpx for regular pages
        response = await self.http_client.get(url)
        response.raise_for_status()
        return response.text

    @retry_with_backoff(max_retries=3, initial_delay=1.0, max_delay=8.0)
    async def _fetch_html_with_retry(self, url: str, use_playwright: bool = False) -> str:
        """
        Internal method to fetch HTML (retry logic applied via decorator)
        
        Args:
            url: URL to fetch
            use_playwright: Whether to use Playwright for JavaScript-rendered pages
            
        Returns:
            HTML content as string
        """
        if use_playwright:
            # Use Playwright for JavaScript-rendered pages
            try:
                from playwright.async_api import async_playwright
                
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()
                    await page.goto(url, wait_until='networkidle', timeout=30000)
                    html = await page.content()
                    await browser.close()
                    return html
            except ImportError:
                logger.warning("playwright_not_installed", url=url)
                # Fallback to httpx
                pass
        
        # Use httpx for regular pages
        response = await self.http_client.get(url)
        response.raise_for_status()
        return response.text

    def _get_cache_key(self, url: str) -> str:
        """
        Generate cache key for URL
        
        Args:
            url: URL to cache
            
        Returns:
            Cache key string
        """
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return f"doc:html:{self.vendor}:{url_hash}"
    
    async def _get_cached_html(self, cache_key: str) -> Optional[str]:
        """
        Get cached HTML content from Redis
        
        Args:
            cache_key: Cache key
            
        Returns:
            Cached HTML or None
        """
        try:
            import redis
            redis_client = redis.from_url(settings.REDIS_URL)
            cached = redis_client.get(cache_key)
            if cached:
                logger.debug("cache_hit", cache_key=cache_key)
                return cached.decode('utf-8')
        except Exception as e:
            logger.warning("cache_get_error", error=str(e))
        return None
    
    async def _set_cached_html(self, cache_key: str, html: str, ttl: int = 86400) -> None:
        """
        Cache HTML content in Redis
        
        Args:
            cache_key: Cache key
            html: HTML content to cache
            ttl: Time to live in seconds (default 24 hours)
        """
        try:
            import redis
            redis_client = redis.from_url(settings.REDIS_URL)
            redis_client.setex(cache_key, ttl, html)
            logger.debug("cache_set", cache_key=cache_key, ttl=ttl)
        except Exception as e:
            logger.warning("cache_set_error", error=str(e))
    
    async def _invalidate_cache(self, url: Optional[str] = None) -> None:
        """
        Invalidate cache for URL or all vendor cache
        
        Args:
            url: Optional specific URL to invalidate
        """
        try:
            import redis
            redis_client = redis.from_url(settings.REDIS_URL)
            
            if url:
                cache_key = self._get_cache_key(url)
                redis_client.delete(cache_key)
                logger.debug("cache_invalidated", cache_key=cache_key)
            else:
                # Invalidate all cache for this vendor
                pattern = f"doc:html:{self.vendor}:*"
                keys = redis_client.keys(pattern)
                if keys:
                    redis_client.delete(*keys)
                    logger.info("cache_invalidated_all", vendor=self.vendor, count=len(keys))
        except Exception as e:
            logger.warning("cache_invalidation_error", error=str(e))

    async def fetch_html(self, url: str, use_playwright: bool = False, use_cache: bool = True) -> str:
        """
        Fetch HTML content from URL with retry logic, rate limiting, and caching
        
        Args:
            url: URL to fetch
            use_playwright: Whether to use Playwright for JavaScript-rendered pages
            use_cache: Whether to use cache (default True)
            
        Returns:
            HTML content as string
        """
        cache_key = self._get_cache_key(url)
        
        # Try to get from cache first
        if use_cache:
            cached_html = await self._get_cached_html(cache_key)
            if cached_html:
                return cached_html
        
        # Fetch with rate limiting and retry
        self._rate_limit()
        html = await self._fetch_html_with_retry(url, use_playwright=use_playwright)
        
        # Cache the result
        if use_cache:
            await self._set_cached_html(cache_key, html)
        
        return html
    
    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()

    def should_scrape(self, url: str) -> bool:
        """
        Determine if URL should be scraped
        
        Args:
            url: URL to check
            
        Returns:
            True if should scrape, False otherwise
        """
        # Skip common non-content URLs
        skip_patterns = [
            '/api/',
            '/search',
            '/login',
            '/logout',
            '/signup',
            '.pdf',
            '.zip',
            '.jpg',
            '.png',
            '.gif',
            '.svg',
        ]
        
        url_lower = url.lower()
        for pattern in skip_patterns:
            if pattern in url_lower:
                return False
        
        return True

    def extract_metadata(self, html: str, url: str) -> Dict[str, Any]:
        """
        Extract metadata from HTML
        
        Args:
            html: HTML content
            url: Page URL
            
        Returns:
            Metadata dictionary
        """
        soup = BeautifulSoup(html, 'html.parser')
        metadata = {
            "url": url,
            "vendor": self.vendor,
            "scraped_at": datetime.utcnow().isoformat(),
        }
        
        # Extract meta tags
        meta_title = soup.find('meta', property='og:title')
        if meta_title:
            metadata["og_title"] = meta_title.get('content', '')
        
        meta_description = soup.find('meta', property='og:description')
        if meta_description:
            metadata["description"] = meta_description.get('content', '')
        
        # Extract canonical URL
        canonical = soup.find('link', rel='canonical')
        if canonical:
            metadata["canonical_url"] = canonical.get('href', '')
        
        return metadata

