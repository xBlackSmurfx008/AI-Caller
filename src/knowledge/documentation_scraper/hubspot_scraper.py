"""HubSpot documentation scraper"""

import re
from typing import List, Dict, Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.knowledge.documentation_scraper.base_scraper import BaseScraper
from src.utils.logging import get_logger

logger = get_logger(__name__)


class HubSpotScraper(BaseScraper):
    """Scraper for HubSpot documentation"""

    def __init__(self):
        """Initialize HubSpot scraper"""
        super().__init__(
            vendor="hubspot",
            base_url="https://developers.hubspot.com",
            rate_limit_delay=1.0
        )

    def get_start_urls(self) -> List[str]:
        """Get HubSpot documentation starting URLs"""
        return [
            "https://developers.hubspot.com/docs/api/overview",
            "https://developers.hubspot.com/docs/api/crm/contacts",
            "https://developers.hubspot.com/docs/api/webhooks",
            "https://developers.hubspot.com/docs/api/crm/deals",
            "https://developers.hubspot.com/docs/api/crm/companies",
            "https://developers.hubspot.com/docs/api/integrations",
        ]

    def extract_links(self, html: str, current_url: str) -> List[str]:
        """Extract links from HubSpot documentation"""
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
            
            # Only include developer docs
            if 'developers.hubspot.com/docs' in full_url:
                normalized = self.normalize_url(full_url)
                if self.should_scrape(normalized):
                    links.append(normalized)
        
        return list(set(links))  # Remove duplicates

    async def extract_content(self, html: str, url: str) -> Dict[str, Any]:
        """Extract content from HubSpot documentation page"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove navigation and sidebar
        for nav in soup.find_all(['nav', 'aside', 'header', 'footer']):
            nav.decompose()
        
        # Extract title
        title = "HubSpot Documentation"
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
        
        # Extract CRM object type
        crm_object = None
        if '/crm/' in url:
            parts = url.split('/crm/')
            if len(parts) > 1:
                crm_object = parts[1].split('/')[0]
        
        # Determine doc type
        doc_type = "api_reference"
        if '/guide' in url or '/tutorial' in url:
            doc_type = "guide"
        elif '/quickstart' in url:
            doc_type = "tutorial"
        elif '/examples' in url or 'example' in url.lower():
            doc_type = "example"
        
        # Extract metadata
        metadata = self.extract_metadata(html, url)
        metadata.update({
            "doc_type": doc_type,
            "endpoint": endpoint,
            "code_blocks": code_blocks,
            "crm_object": crm_object,
            "vendor": "hubspot",
        })
        
        return {
            "title": title,
            "content": content,
            "url": url,
            "metadata": metadata,
            "vendor": "hubspot",
            "doc_type": doc_type,
        }

