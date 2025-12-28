"""HTML document extractor"""

import re
from typing import Dict, Any, Tuple
from pathlib import Path

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from src.knowledge.extractors.base_extractor import BaseExtractor
from src.utils.errors import KnowledgeBaseError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class HTMLExtractor(BaseExtractor):
    """Extract text and metadata from HTML files"""

    def supports(self, file_path: str) -> bool:
        """Check if file is HTML"""
        return Path(file_path).suffix.lower() in [".html", ".htm"]

    def extract(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text and metadata from HTML file
        
        Args:
            file_path: Path to HTML file
            
        Returns:
            Tuple of (content, metadata)
        """
        metadata = self._get_file_metadata(file_path)
        
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                html_content = file.read()
            
            if BS4_AVAILABLE:
                soup = BeautifulSoup(html_content, "html.parser")
                
                # Extract metadata from meta tags
                if soup.title:
                    metadata["title"] = soup.title.string
                
                meta_tags = soup.find_all("meta")
                for meta in meta_tags:
                    name = meta.get("name") or meta.get("property", "").lower()
                    content = meta.get("content", "")
                    if name and content:
                        metadata[name] = content
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                
                # Extract text preserving structure
                content_parts = []
                
                # Extract headings
                for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
                    level = int(heading.name[1])
                    content_parts.append(f"\n{'#' * level} {heading.get_text().strip()}\n")
                
                # Extract paragraphs
                for para in soup.find_all("p"):
                    text = para.get_text().strip()
                    if text:
                        content_parts.append(text)
                
                # Extract lists
                for ul in soup.find_all(["ul", "ol"]):
                    list_items = []
                    for li in ul.find_all("li"):
                        list_items.append(f"- {li.get_text().strip()}")
                    if list_items:
                        content_parts.append("\n".join(list_items))
                
                content = "\n\n".join(content_parts)
            else:
                # Fallback: simple regex extraction
                content = re.sub(r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL | re.IGNORECASE)
                content = re.sub(r"<[^>]+>", "", content)
                content = re.sub(r"\s+", " ", content)
            
            return content, metadata
            
        except Exception as e:
            logger.error("html_extraction_error", error=str(e), file_path=file_path)
            raise KnowledgeBaseError(f"Failed to extract HTML: {str(e)}") from e

