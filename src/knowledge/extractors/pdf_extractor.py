"""PDF document extractor"""

import re
from typing import Dict, Any, Tuple
from pathlib import Path

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from pdfplumber import PDF
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

from src.knowledge.extractors.base_extractor import BaseExtractor
from src.utils.errors import KnowledgeBaseError
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PDFExtractor(BaseExtractor):
    """Extract text and metadata from PDF files"""

    def supports(self, file_path: str) -> bool:
        """Check if file is a PDF"""
        return Path(file_path).suffix.lower() == ".pdf"

    def extract(self, file_path: str) -> Tuple[str, Dict[str, Any]]:
        """
        Extract text and metadata from PDF
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Tuple of (content, metadata)
        """
        if not PDF_AVAILABLE:
            raise KnowledgeBaseError("PyPDF2 is required for PDF extraction")
        
        metadata = self._get_file_metadata(file_path)
        content_parts = []
        
        try:
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract metadata
                if pdf_reader.metadata:
                    metadata.update({
                        "title": pdf_reader.metadata.get("/Title", ""),
                        "author": pdf_reader.metadata.get("/Author", ""),
                        "subject": pdf_reader.metadata.get("/Subject", ""),
                        "creator": pdf_reader.metadata.get("/Creator", ""),
                        "producer": pdf_reader.metadata.get("/Producer", ""),
                        "creation_date": str(pdf_reader.metadata.get("/CreationDate", "")),
                        "modification_date": str(pdf_reader.metadata.get("/ModDate", "")),
                    })
                
                # Extract text from all pages
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            # Preserve page structure
                            content_parts.append(f"[Page {page_num + 1}]\n{page_text}\n")
                    except Exception as e:
                        logger.warning("page_extraction_failed", page=page_num, error=str(e))
                
                # Try pdfplumber for better table extraction if available
                if PDFPLUMBER_AVAILABLE and len(content_parts) == 0:
                    try:
                        with PDF.open(file_path) as pdf:
                            for page in pdf.pages:
                                page_text = page.extract_text()
                                if page_text:
                                    content_parts.append(page_text)
                                
                                # Extract tables
                                tables = page.extract_tables()
                                if tables:
                                    for table in tables:
                                        table_text = self._format_table(table)
                                        content_parts.append(f"\n[Table]\n{table_text}\n")
                    except Exception as e:
                        logger.warning("pdfplumber_extraction_failed", error=str(e))
                
                content = "\n".join(content_parts)
                metadata["page_count"] = len(pdf_reader.pages)
                metadata["extraction_method"] = "pypdf2"
                
                return content, metadata
                
        except Exception as e:
            logger.error("pdf_extraction_error", error=str(e), file_path=file_path)
            raise KnowledgeBaseError(f"Failed to extract PDF: {str(e)}") from e

    def _format_table(self, table: list) -> str:
        """Format table data as text"""
        if not table:
            return ""
        
        rows = []
        for row in table:
            if row:
                # Filter out None values and join with separator
                row_text = " | ".join(str(cell) if cell else "" for cell in row)
                rows.append(row_text)
        
        return "\n".join(rows)

