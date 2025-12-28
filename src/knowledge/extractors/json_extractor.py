"""JSON document extractor"""

import json
from typing import Dict, Any, Tuple
from pathlib import Path

from src.knowledge.extractors.base_extractor import BaseExtractor
from src.utils.errors import KnowledgeBaseError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class JSONExtractor(BaseExtractor):
    """Extract text and metadata from JSON files"""

    def supports(self, file_path: str) -> bool:
        """Check if file is JSON"""
        return Path(file_path).suffix.lower() == ".json"

    def extract(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text and metadata from JSON file
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Tuple of (content, metadata)
        """
        metadata = self._get_file_metadata(file_path)
        
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            
            # Convert JSON to readable text format
            content = self._json_to_text(data)
            
            # Extract metadata from JSON structure
            if isinstance(data, dict):
                metadata["keys"] = list(data.keys())[:10]  # First 10 keys
                metadata["structure_type"] = "object"
                if "title" in data:
                    metadata["title"] = str(data["title"])
                if "name" in data:
                    metadata["name"] = str(data["name"])
            elif isinstance(data, list):
                metadata["structure_type"] = "array"
                metadata["item_count"] = len(data)
            
            return content, metadata
            
        except json.JSONDecodeError as e:
            logger.error("json_decode_error", error=str(e), file_path=file_path)
            raise KnowledgeBaseError(f"Invalid JSON file: {str(e)}") from e
        except Exception as e:
            logger.error("json_extraction_error", error=str(e), file_path=file_path)
            raise KnowledgeBaseError(f"Failed to extract JSON: {str(e)}") from e

    def _json_to_text(self, data: Any, indent: int = 0) -> str:
        """Convert JSON structure to readable text"""
        indent_str = "  " * indent
        
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{indent_str}{key}:")
                    lines.append(self._json_to_text(value, indent + 1))
                else:
                    lines.append(f"{indent_str}{key}: {value}")
            return "\n".join(lines)
        elif isinstance(data, list):
            lines = []
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    lines.append(f"{indent_str}[{i}]:")
                    lines.append(self._json_to_text(item, indent + 1))
                else:
                    lines.append(f"{indent_str}- {item}")
            return "\n".join(lines)
        else:
            return f"{indent_str}{data}"

