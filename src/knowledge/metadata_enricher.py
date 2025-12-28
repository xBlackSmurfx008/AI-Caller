"""Metadata extraction and enrichment system"""

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


class MetadataEnricher:
    """Enrich document metadata with extracted information"""

    def __init__(self):
        """Initialize metadata enricher"""
        self.domain_keywords = {
            "technical": ["api", "code", "function", "class", "method", "algorithm", "database", "server"],
            "business": ["revenue", "profit", "customer", "sales", "marketing", "strategy", "budget"],
            "legal": ["contract", "agreement", "terms", "liability", "warranty", "compliance", "regulation"],
            "support": ["troubleshooting", "error", "issue", "problem", "solution", "help", "guide"],
        }

    def enrich(
        self,
        content: str,
        existing_metadata: Optional[Dict[str, Any]] = None,
        source_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Enrich metadata from content
        
        Args:
            content: Document content
            existing_metadata: Existing metadata to enhance
            source_type: Type of source document
            
        Returns:
            Enriched metadata dictionary
        """
        if existing_metadata is None:
            existing_metadata = {}
        
        enriched = existing_metadata.copy()
        
        # Basic content metadata
        enriched.update(self._extract_content_metadata(content))
        
        # Domain classification
        enriched["domain"] = self._classify_domain(content)
        
        # Language detection
        if LANGDETECT_AVAILABLE:
            enriched["language"] = self._detect_language(content)
        
        # Content quality scores
        enriched["quality_scores"] = self._calculate_quality_scores(content)
        
        # Temporal metadata
        enriched.update(self._extract_temporal_metadata(content))
        
        # Entity extraction (simplified)
        enriched["entities"] = self._extract_entities(content)
        
        # Content type classification
        enriched["content_type"] = self._classify_content_type(content, source_type)
        
        # Confidence score
        enriched["confidence"] = self._calculate_confidence(enriched)
        
        return enriched

    def _extract_content_metadata(self, content: str) -> Dict[str, Any]:
        """Extract basic content metadata"""
        return {
            "content_length": len(content),
            "word_count": len(content.split()),
            "sentence_count": len(re.findall(r'[.!?]+', content)),
            "paragraph_count": len([p for p in content.split('\n\n') if p.strip()]),
            "has_code": bool(re.search(r'```|def |class |function ', content)),
            "has_tables": bool(re.search(r'\|.*\|', content)),
            "has_lists": bool(re.search(r'^\s*[-*•]\s+', content, re.MULTILINE)),
            "has_urls": bool(re.search(r'http[s]?://', content)),
            "has_emails": bool(re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)),
        }

    def _classify_domain(self, content: str) -> str:
        """Classify document domain"""
        content_lower = content.lower()
        domain_scores = {}
        
        for domain, keywords in self.domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            domain_scores[domain] = score
        
        if domain_scores:
            return max(domain_scores.items(), key=lambda x: x[1])[0]
        
        return "general"

    def _detect_language(self, content: str) -> Dict[str, Any]:
        """Detect document language"""
        if not LANGDETECT_AVAILABLE:
            return {"code": "unknown", "confidence": 0.0}
        
        try:
            lang_code = langdetect.detect(content)
            # Simple confidence estimation
            confidence = min(len(content) / 1000, 1.0)
            return {"code": lang_code, "confidence": confidence}
        except Exception as e:
            logger.warning("language_detection_failed", error=str(e))
            return {"code": "unknown", "confidence": 0.0}

    def _calculate_quality_scores(self, content: str) -> Dict[str, float]:
        """Calculate content quality scores"""
        scores = {}
        
        # Readability score (simplified)
        words = content.split()
        sentences = re.findall(r'[.!?]+', content)
        if sentences and words:
            avg_words_per_sentence = len(words) / len(sentences)
            # Flesch-like score (simplified)
            readability = max(0, min(100, 206.835 - (1.015 * avg_words_per_sentence)))
            scores["readability"] = readability / 100.0
        else:
            scores["readability"] = 0.5
        
        # Completeness score
        has_title = bool(re.search(r'^#+\s+', content, re.MULTILINE))
        has_structure = bool(re.search(r'^#{1,6}\s+', content, re.MULTILINE))
        has_content = len(content.strip()) > 100
        completeness = sum([has_title, has_structure, has_content]) / 3.0
        scores["completeness"] = completeness
        
        # Coherence score (simplified - based on sentence structure)
        sentence_count = len(sentences)
        if sentence_count > 0:
            # Check for proper sentence endings
            proper_endings = sum(1 for s in sentences if s.strip())
            coherence = proper_endings / sentence_count if sentence_count > 0 else 0.5
        else:
            coherence = 0.5
        scores["coherence"] = coherence
        
        # Overall quality
        scores["overall"] = sum(scores.values()) / len(scores)
        
        return scores

    def _extract_temporal_metadata(self, content: str) -> Dict[str, Any]:
        """Extract temporal information"""
        metadata = {}
        
        # Extract dates
        date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
        ]
        
        dates = []
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, content, re.IGNORECASE))
        
        if dates:
            metadata["dates_found"] = list(set(dates))
            # Try to extract most recent date as document date
            try:
                # Simple heuristic: use the last date found
                metadata["document_date"] = dates[-1]
            except Exception:
                pass
        
        # Extract time references
        time_patterns = [
            r'\b\d{1,2}:\d{2}(?:\s*[AP]M)?\b',
            r'\b(?:morning|afternoon|evening|night)\b',
        ]
        
        times = []
        for pattern in time_patterns:
            times.extend(re.findall(pattern, content, re.IGNORECASE))
        
        if times:
            metadata["times_found"] = list(set(times))
        
        return metadata

    def _extract_entities(self, content: str) -> Dict[str, List[str]]:
        """Extract entities from content (simplified)"""
        entities = {
            "emails": [],
            "urls": [],
            "phone_numbers": [],
            "organizations": [],
            "locations": [],
        }
        
        # Extract emails
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
        entities["emails"] = list(set(emails))
        
        # Extract URLs
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
        entities["urls"] = list(set(urls))
        
        # Extract phone numbers
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phones = re.findall(phone_pattern, content)
        entities["phone_numbers"] = list(set(phones))
        
        # Extract potential organizations (capitalized words)
        org_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
        orgs = re.findall(org_pattern, content)
        # Filter out common false positives
        false_positives = {"The", "This", "That", "These", "Those", "There", "Here"}
        entities["organizations"] = [org for org in orgs if org.split()[0] not in false_positives][:10]
        
        return entities

    def _classify_content_type(self, content: str, source_type: Optional[str] = None) -> str:
        """Classify content type"""
        content_lower = content.lower()
        
        # Check for code
        if re.search(r'```|def |class |function |import |from ', content):
            return "code"
        
        # Check for structured data
        if re.search(r'\|.*\|', content) or re.search(r'^\s*[-*•]\s+', content, re.MULTILINE):
            return "structured"
        
        # Check for conversational
        if re.search(r'Q:|A:|Question:|Answer:', content, re.IGNORECASE):
            return "conversational"
        
        # Check for documentation
        if re.search(r'^#+\s+', content, re.MULTILINE) or source_type == "md":
            return "documentation"
        
        # Default based on source type
        type_mapping = {
            "pdf": "document",
            "docx": "document",
            "txt": "text",
            "html": "web",
            "csv": "data",
            "json": "data",
        }
        
        return type_mapping.get(source_type or "", "general")

    def _calculate_confidence(self, metadata: Dict[str, Any]) -> float:
        """Calculate overall confidence score for metadata"""
        confidence_factors = []
        
        # Language detection confidence
        if "language" in metadata and isinstance(metadata["language"], dict):
            confidence_factors.append(metadata["language"].get("confidence", 0.5))
        
        # Quality scores
        if "quality_scores" in metadata:
            quality = metadata["quality_scores"].get("overall", 0.5)
            confidence_factors.append(quality)
        
        # Content completeness
        if "content_length" in metadata:
            length_score = min(metadata["content_length"] / 1000, 1.0)
            confidence_factors.append(length_score)
        
        # Domain classification confidence
        if "domain" in metadata:
            confidence_factors.append(0.7)  # Simplified
        
        if confidence_factors:
            return sum(confidence_factors) / len(confidence_factors)
        
        return 0.5

    def merge_metadata(
        self,
        base_metadata: Dict[str, Any],
        additional_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Merge metadata dictionaries intelligently
        
        Args:
            base_metadata: Base metadata
            additional_metadata: Additional metadata to merge
            
        Returns:
            Merged metadata
        """
        merged = base_metadata.copy()
        
        for key, value in additional_metadata.items():
            if key not in merged:
                merged[key] = value
            elif isinstance(merged[key], dict) and isinstance(value, dict):
                # Merge nested dictionaries
                merged[key] = {**merged[key], **value}
            elif isinstance(merged[key], list) and isinstance(value, list):
                # Merge lists (avoid duplicates)
                merged[key] = list(set(merged[key] + value))
            else:
                # Prefer non-None values
                if value is not None:
                    merged[key] = value
        
        return merged

