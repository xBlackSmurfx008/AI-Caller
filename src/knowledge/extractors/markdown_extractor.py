"""Markdown document extractor"""

from typing import Dict, Any, Tuple
from pathlib import Path

from src.knowledge.extractors.base_extractor import BaseExtractor
from src.utils.errors import KnowledgeBaseError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class MarkdownExtractor(BaseExtractor):
    """Extract text and metadata from Markdown files"""

    def supports(self, file_path: str) -> bool:
        """Check if file is Markdown"""
        return Path(file_path).suffix.lower() in [".md", ".markdown"]

    def extract(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text and metadata from Markdown file
        
        Args:
            file_path: Path to Markdown file
            
        Returns:
            Tuple of (content, metadata)
        """
        metadata = self._get_file_metadata(file_path)
        
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            
            # Extract frontmatter if present
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    content = parts[2]
                    
                    # Parse YAML frontmatter (simple parsing)
                    for line in frontmatter.split("\n"):
                        if ":" in line:
                            key, value = line.split(":", 1)
                            metadata[key.strip()] = value.strip().strip('"').strip("'")
            
            # Extract title from first heading
            lines = content.split("\n")
            for line in lines[:10]:  # Check first 10 lines
                if line.startswith("#"):
                    metadata["title"] = line.lstrip("#").strip()
                    break
            
            metadata["line_count"] = len(lines)
            metadata["heading_count"] = sum(1 for line in lines if line.startswith("#"))
            
            return content, metadata
            
        except Exception as e:
            logger.error("markdown_extraction_error", error=str(e), file_path=file_path)
            raise KnowledgeBaseError(f"Failed to extract Markdown: {str(e)}") from e

