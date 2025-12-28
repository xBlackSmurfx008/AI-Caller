"""OpenAI documentation scraper"""

import re
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from src.knowledge.documentation_scraper.base_scraper import BaseScraper
from src.utils.logging import get_logger

logger = get_logger(__name__)


class OpenAIScraper(BaseScraper):
    """Scraper for OpenAI documentation"""

    def __init__(self):
        """Initialize OpenAI scraper"""
        super().__init__(
            vendor="openai",
            base_url="https://platform.openai.com",
            rate_limit_delay=1.0
        )
        self.base_docs_url = "https://platform.openai.com/docs"

    def get_start_urls(self) -> List[str]:
        """Get OpenAI documentation starting URLs"""
        return [
            "https://platform.openai.com/docs/api-reference",
            "https://platform.openai.com/docs/guides/voice",
            "https://platform.openai.com/docs/guides/realtime",
            "https://platform.openai.com/docs/guides/embeddings",
            "https://platform.openai.com/docs/guides/text-generation",
            "https://platform.openai.com/docs/guides/function-calling",
            "https://platform.openai.com/docs/guides/error-handling",
            "https://platform.openai.com/docs/guides/best-practices",
        ]

    def extract_links(self, html: str, current_url: str) -> List[str]:
        """Extract links from OpenAI documentation"""
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
            
            # Only include docs links
            if 'platform.openai.com/docs' in full_url:
                normalized = self.normalize_url(full_url)
                if self.should_scrape(normalized):
                    links.append(normalized)
        
        return list(set(links))  # Remove duplicates

    async def extract_content(self, html: str, url: str) -> Dict[str, Any]:
        """Extract content from OpenAI documentation page"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove navigation and sidebar
        for nav in soup.find_all(['nav', 'aside', 'header', 'footer']):
            nav.decompose()
        
        # Extract title
        title = "OpenAI Documentation"
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
        
        # Extract API version
        api_version = None
        version_match = re.search(r'v\d+', url)
        if version_match:
            api_version = version_match.group(0)
        
        # Determine doc type
        doc_type = "api_reference"
        if '/guides/' in url:
            doc_type = "guide"
        elif '/examples/' in url or 'example' in url.lower():
            doc_type = "example"
        elif '/troubleshooting' in url or 'error' in url.lower():
            doc_type = "troubleshooting"
        
        # Extract metadata
        metadata = self.extract_metadata(html, url)
        metadata.update({
            "doc_type": doc_type,
            "api_version": api_version,
            "endpoint": endpoint,
            "code_blocks": code_blocks,
            "vendor": "openai",
        })
        
        return {
            "title": title,
            "content": content,
            "url": url,
            "metadata": metadata,
            "vendor": "openai",
            "doc_type": doc_type,
        }

