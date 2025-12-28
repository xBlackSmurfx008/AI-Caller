"""CSV document extractor"""

import csv
from typing import Dict, Any, Tuple
from pathlib import Path

from src.knowledge.extractors.base_extractor import BaseExtractor
from src.utils.errors import KnowledgeBaseError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class CSVExtractor(BaseExtractor):
    """Extract text and metadata from CSV files"""

    def supports(self, file_path: str) -> bool:
        """Check if file is CSV"""
        return Path(file_path).suffix.lower() == ".csv"

    def extract(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text and metadata from CSV file
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            Tuple of (content, metadata)
        """
        metadata = self._get_file_metadata(file_path)
        content_parts = []
        
        try:
            with open(file_path, "r", encoding="utf-8", newline="") as file:
                # Try to detect delimiter
                sample = file.read(1024)
                file.seek(0)
                sniffer = csv.Sniffer()
                delimiter = sniffer.sniff(sample).delimiter
                
                reader = csv.reader(file, delimiter=delimiter)
                rows = list(reader)
                
                if rows:
                    # First row as header
                    header = rows[0]
                    metadata["columns"] = header
                    metadata["column_count"] = len(header)
                    
                    # Format as table
                    content_parts.append(" | ".join(header))
                    content_parts.append(" | ".join(["---"] * len(header)))
                    
                    for row in rows[1:]:
                        # Pad row to match header length
                        padded_row = row + [""] * (len(header) - len(row))
                        content_parts.append(" | ".join(str(cell) for cell in padded_row[:len(header)]))
                    
                    metadata["row_count"] = len(rows) - 1
            
            content = "\n".join(content_parts)
            return content, metadata
            
        except Exception as e:
            logger.error("csv_extraction_error", error=str(e), file_path=file_path)
            raise KnowledgeBaseError(f"Failed to extract CSV: {str(e)}") from e

