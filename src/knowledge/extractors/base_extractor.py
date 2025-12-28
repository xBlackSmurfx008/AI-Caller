"""Base extractor class for document extraction"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple
from pathlib import Path


class BaseExtractor(ABC):
    """Base class for document extractors"""

    @abstractmethod
    def extract(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text and metadata from a file
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (content, metadata)
        """
        pass

    @abstractmethod
    def supports(self, file_path: str) -> bool:
        """
        Check if this extractor supports the given file
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if supported, False otherwise
        """
        pass

    def _get_file_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Get basic file metadata
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary of metadata
        """
        path = Path(file_path)
        return {
            "file_name": path.name,
            "file_extension": path.suffix.lower(),
            "file_size": path.stat().st_size if path.exists() else 0,
        }

