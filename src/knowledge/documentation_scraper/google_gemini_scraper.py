"""Google Gemini documentation scraper"""

import re
from typing import List, Dict, Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.knowledge.documentation_scraper.base_scraper import BaseScraper
from src.utils.logging import get_logger

logger = get_logger(__name__)


class GoogleGeminiScraper(BaseScraper):
    """Scraper for Google Gemini/Google AI documentation"""

    def __init__(self):
        """Initialize Google Gemini scraper"""
        super().__init__(
            vendor="google",
            base_url="https://ai.google.dev",
            rate_limit_delay=1.0
        )

    def get_start_urls(self) -> List[str]:
        """Get Google Gemini documentation starting URLs"""
        return [
            "https://ai.google.dev/docs",
            "https://ai.google.dev/gemini-api/docs",
            "https://ai.google.dev/gemini-api/docs/get-started",
            "https://ai.google.dev/gemini-api/docs/quickstart",
            "https://ai.google.dev/gemini-api/docs/models",
            "https://ai.google.dev/gemini-api/docs/function-calling",
            "https://ai.google.dev/gemini-api/docs/safety-settings",
        ]

    def extract_links(self, html: str, current_url: str) -> List[str]:
        """Extract links from Google Gemini documentation"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                full_url = urljoin(self.base_url, href)
            elif href.startswith('http'):
                full_url = href
            else:
                full_url = urljoin(current_url, href)
            
            # Only include AI docs
            if 'ai.google.dev' in full_url:
                normalized = self.normalize_url(full_url)
                if self.should_scrape(normalized):
                    links.append(normalized)
        
        return list(set(links))  # Remove duplicates

    async def extract_content(self, html: str, url: str) -> Dict[str, Any]:
        """Extract content from Google Gemini documentation page"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove navigation and sidebar
        for nav in soup.find_all(['nav', 'aside', 'header', 'footer']):
            nav.decompose()
        
        # Extract title
        title = "Google AI Documentation"
        h1 = soup.find('h1')
        if h1:
            title = h1.get_text().strip()
        else:
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
        
        # Extract main content
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile('content|main|article'))
        if not main_content:
            main_content = soup.find('body')
        
        # Extract code examples
        code_blocks = self.extract_code_blocks(html)
        
        # Convert to markdown
        content = self.html_to_markdown(str(main_content) if main_content else html)
        
        # Extract API endpoint if present
        endpoint = None
        endpoint_match = re.search(r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-]+)', content)
        if endpoint_match:
            endpoint = endpoint_match.group(2)
        
        # Extract model name if present
        model_name = None
        model_match = re.search(r'(gemini-[a-z0-9-]+)', content, re.IGNORECASE)
        if model_match:
            model_name = model_match.group(1)
        
        # Determine doc type
        doc_type = "api_reference"
        if '/get-started' in url or '/quickstart' in url:
            doc_type = "tutorial"
        elif '/guide' in url:
            doc_type = "guide"
        elif '/examples' in url or 'example' in url.lower():
            doc_type = "example"
        
        # Extract metadata
        metadata = self.extract_metadata(html, url)
        metadata.update({
            "doc_type": doc_type,
            "endpoint": endpoint,
            "code_blocks": code_blocks,
            "model_name": model_name,
            "vendor": "google",
        })
        
        return {
            "title": title,
            "content": content,
            "url": url,
            "metadata": metadata,
            "vendor": "google",
            "doc_type": doc_type,
        }

