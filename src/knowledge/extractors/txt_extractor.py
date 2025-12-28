"""TXT document extractor"""

from typing import Dict, Any, Tuple
from pathlib import Path

from src.knowledge.extractors.base_extractor import BaseExtractor
from src.utils.errors import KnowledgeBaseError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class TXTExtractor(BaseExtractor):
    """Extract text and metadata from TXT files"""

    def supports(self, file_path: str) -> bool:
        """Check if file is a TXT"""
        return Path(file_path).suffix.lower() == ".txt"

    def extract(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text and metadata from TXT file
        
        Args:
            file_path: Path to TXT file
            
        Returns:
            Tuple of (content, metadata)
        """
        metadata = self._get_file_metadata(file_path)
        
        try:
            # Try different encodings
            encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding) as file:
                        content = file.read()
                        metadata["encoding"] = encoding
                        break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                raise KnowledgeBaseError("Could not decode TXT file with any supported encoding")
            
            # Try to extract title from first line
            lines = content.split("\n")
            if lines and len(lines[0].strip()) < 100:
                metadata["title"] = lines[0].strip()
            
            metadata["line_count"] = len(lines)
            metadata["word_count"] = len(content.split())
            
            return content, metadata
            
        except Exception as e:
            logger.error("txt_extraction_error", error=str(e), file_path=file_path)
            raise KnowledgeBaseError(f"Failed to extract TXT: {str(e)}") from e

