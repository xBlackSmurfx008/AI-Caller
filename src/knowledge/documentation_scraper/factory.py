"""Factory for creating documentation scrapers"""

import threading
from typing import Dict, Optional
import httpx

from src.knowledge.documentation_scraper.base_scraper import BaseScraper
from src.knowledge.documentation_scraper.openai_scraper import OpenAIScraper
from src.knowledge.documentation_scraper.twilio_scraper import TwilioScraper
from src.knowledge.documentation_scraper.ringcentral_scraper import RingCentralScraper
from src.knowledge.documentation_scraper.hubspot_scraper import HubSpotScraper
from src.knowledge.documentation_scraper.google_gemini_scraper import GoogleGeminiScraper
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DocumentationScraperFactory:
    """Factory for creating and managing documentation scrapers"""
    
    _instance: Optional['DocumentationScraperFactory'] = None
    _lock = threading.Lock()
    _http_client: Optional[httpx.AsyncClient] = None
    _http_client_lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._scrapers: Dict[str, BaseScraper] = {}
        return cls._instance
    
    @classmethod
    def get_http_client(cls) -> httpx.AsyncClient:
        """Get or create shared HTTP client (singleton)"""
        if cls._http_client is None:
            with cls._http_client_lock:
                if cls._http_client is None:
                    cls._http_client = httpx.AsyncClient(
                        timeout=30.0,
                        follow_redirects=True,
                        headers={
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                        }
                    )
                    logger.info("http_client_created")
        return cls._http_client
    
    def create_scraper(self, vendor: str) -> BaseScraper:
        """
        Create or get existing scraper for vendor
        
        Args:
            vendor: Vendor name (openai, twilio, etc.)
            
        Returns:
            Scraper instance
            
        Raises:
            ValueError: If vendor is not supported
        """
        vendor = vendor.lower()
        
        # Return existing scraper if available
        if vendor in self._scrapers:
            return self._scrapers[vendor]
        
        # Create new scraper
        with self._lock:
            # Double-check after acquiring lock
            if vendor in self._scrapers:
                return self._scrapers[vendor]
            
            scraper = self._create_scraper_instance(vendor)
            self._scrapers[vendor] = scraper
            logger.info("scraper_created", vendor=vendor)
            return scraper
    
    def _create_scraper_instance(self, vendor: str) -> BaseScraper:
        """
        Create scraper instance for vendor
        
        Args:
            vendor: Vendor name
            
        Returns:
            Scraper instance
        """
        vendor_map = {
            "openai": OpenAIScraper,
            "twilio": TwilioScraper,
            "ringcentral": RingCentralScraper,
            "hubspot": HubSpotScraper,
            "google": GoogleGeminiScraper,
        }
        
        scraper_class = vendor_map.get(vendor)
        if not scraper_class:
            raise ValueError(f"Unsupported vendor: {vendor}. Supported vendors: {', '.join(vendor_map.keys())}")
        
        return scraper_class()
    
    def get_all_vendors(self) -> list[str]:
        """Get list of all supported vendors"""
        return ["openai", "twilio", "ringcentral", "hubspot", "google"]
    
    async def cleanup(self):
        """Cleanup resources (close HTTP clients)"""
        # Close scrapers' HTTP clients
        for scraper in self._scrapers.values():
            if hasattr(scraper, 'close'):
                await scraper.close()
        
        # Close shared HTTP client
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
            logger.info("http_client_closed")
    
    def clear_cache(self):
        """Clear scraper cache (force recreation)"""
        with self._lock:
            self._scrapers.clear()
            logger.info("scraper_cache_cleared")


# Global factory instance
_factory = DocumentationScraperFactory()


def get_scraper_factory() -> DocumentationScraperFactory:
    """Get global scraper factory instance"""
    return _factory


def get_scraper(vendor: str) -> BaseScraper:
    """Convenience function to get scraper for vendor"""
    return _factory.create_scraper(vendor)

