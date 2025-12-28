"""Document preprocessing pipeline for normalization and cleaning"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime

try:
    import langdetect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

from src.utils.logging import get_logger

logger = get_logger(__name__)


class DocumentPreprocessor:
    """Preprocess documents before chunking and embedding"""

    def __init__(self):
        """Initialize preprocessor"""
        self.noise_patterns = [
            r'Page \d+',  # Page numbers
            r'\d+/\d+/\d+',  # Dates in various formats
            r'© \d{4}',  # Copyright notices
            r'Confidential|Proprietary',  # Confidentiality notices
        ]

    def preprocess(
        self,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        remove_noise: bool = True,
        normalize_whitespace: bool = True,
        detect_language: bool = True,
    ) -> tuple[str, Dict[str, Any]]:
        """
        Preprocess document content
        
        Args:
            content: Raw document content
            metadata: Existing metadata (will be enhanced)
            remove_noise: Whether to remove noise patterns
            normalize_whitespace: Whether to normalize whitespace
            detect_language: Whether to detect language
            
        Returns:
            Tuple of (processed_content, enhanced_metadata)
        """
        if metadata is None:
            metadata = {}
        
        processed_content = content
        
        # Language detection
        if detect_language and LANGDETECT_AVAILABLE:
            try:
                detected_lang = langdetect.detect(processed_content)
                metadata["language"] = detected_lang
                metadata["language_confidence"] = 1.0  # Simplified
            except Exception as e:
                logger.warning("language_detection_failed", error=str(e))
                metadata["language"] = "unknown"
        
        # Remove noise patterns
        if remove_noise:
            processed_content = self._remove_noise(processed_content, metadata)
        
        # Normalize whitespace
        if normalize_whitespace:
            processed_content = self._normalize_whitespace(processed_content)
        
        # Detect and handle duplicates
        metadata["duplicate_score"] = self._detect_duplicates(processed_content)
        
        # Extract additional metadata
        metadata.update(self._extract_metadata(processed_content))
        
        # Calculate content statistics
        metadata.update(self._calculate_statistics(processed_content))
        
        return processed_content, metadata

    def _remove_noise(self, content: str, metadata: Dict[str, Any]) -> str:
        """Remove noise patterns from content"""
        removed_patterns = []
        
        for pattern in self.noise_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                removed_patterns.extend(matches)
                content = re.sub(pattern, "", content, flags=re.IGNORECASE)
        
        if removed_patterns:
            metadata["removed_patterns"] = list(set(removed_patterns))
        
        return content

    def _normalize_whitespace(self, content: str) -> str:
        """Normalize whitespace in content"""
        # Replace multiple spaces with single space
        content = re.sub(r' +', ' ', content)
        
        # Replace multiple newlines with double newline (paragraph break)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in content.split('\n')]
        content = '\n'.join(lines)
        
        # Remove leading/trailing whitespace
        content = content.strip()
        
        return content

    def _detect_duplicates(self, content: str) -> float:
        """
        Detect duplicate content within document
        
        Returns:
            Duplicate score between 0 and 1 (higher = more duplicates)
        """
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if len(sentences) < 2:
            return 0.0
        
        # Simple duplicate detection: check for exact sentence matches
        unique_sentences = set(sentences)
        duplicate_ratio = 1.0 - (len(unique_sentences) / len(sentences))
        
        return min(duplicate_ratio, 1.0)

    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from content"""
        metadata = {}
        
        # Extract email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        if emails:
            metadata["emails"] = list(set(emails))
        
        # Extract URLs
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
        if urls:
            metadata["urls"] = list(set(urls))
        
        # Extract phone numbers (simple pattern)
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phones = re.findall(phone_pattern, content)
        if phones:
            metadata["phone_numbers"] = list(set(phones))
        
        # Extract dates
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',  # Month DD, YYYY
        ]
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, content, re.IGNORECASE))
        if dates:
            metadata["dates"] = list(set(dates))
        
        # Detect code blocks
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        if code_blocks:
            metadata["has_code"] = True
            metadata["code_block_count"] = len(code_blocks)
        
        # Detect lists
        list_items = re.findall(r'^\s*[-*•]\s+', content, re.MULTILINE)
        if list_items:
            metadata["has_lists"] = True
            metadata["list_item_count"] = len(list_items)
        
        return metadata

    def _calculate_statistics(self, content: str) -> Dict[str, Any]:
        """Calculate content statistics"""
        stats = {
            "character_count": len(content),
            "word_count": len(content.split()),
            "sentence_count": len(re.findall(r'[.!?]+', content)),
            "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
            "average_word_length": sum(len(word) for word in content.split()) / max(len(content.split()), 1),
            "average_sentence_length": len(content.split()) / max(len(re.findall(r'[.!?]+', content)), 1),
        }
        
        return stats

    def clean_headers_footers(self, content: str, lines: Optional[List[str]] = None) -> str:
        """
        Remove headers and footers from content
        
        Args:
            content: Document content
            lines: Optional pre-split lines (for efficiency)
            
        Returns:
            Cleaned content
        """
        if lines is None:
            lines = content.split('\n')
        
        # Remove common header/footer patterns
        # Headers typically appear in first few lines
        # Footers typically appear in last few lines
        
        # Simple heuristic: remove lines that appear multiple times
        line_counts = {}
        for line in lines:
            stripped = line.strip()
            if len(stripped) > 5:  # Ignore very short lines
                line_counts[stripped] = line_counts.get(stripped, 0) + 1
        
        # Remove lines that appear more than once (likely headers/footers)
        cleaned_lines = []
        for line in lines:
            if line_counts.get(line.strip(), 0) <= 1 or len(line.strip()) <= 5:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)

