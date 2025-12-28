"""Compliance checking for call interactions"""

import re
from typing import Dict, Any, List

from src.utils.logging import get_logger

logger = get_logger(__name__)


class ComplianceChecker:
    """Compliance checking for AI responses"""

    def __init__(self):
        """Initialize compliance checker"""
        # Patterns for compliance violations
        self.pii_patterns = [
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\b\d{16}\b",  # Credit card
            r"\b\d{4}\s\d{4}\s\d{4}\s\d{4}\b",  # Credit card with spaces
        ]

        # Prohibited phrases
        self.prohibited_phrases = [
            "guaranteed profit",
            "risk-free investment",
            "act now or lose",
            "limited time only",
        ]

        # Required disclosures (industry-specific)
        self.required_disclosures = []

    def check(self, text: str) -> Dict[str, Any]:
        """
        Check text for compliance issues
        
        Args:
            text: Text to check
            
        Returns:
            Dictionary with compliance check results
        """
        issues = []

        # Check for PII
        pii_found = self._check_pii(text)
        if pii_found:
            issues.append("potential_pii_exposure")

        # Check for prohibited phrases
        prohibited_found = self._check_prohibited(text)
        if prohibited_found:
            issues.append("prohibited_language")

        # Check for required disclosures (if applicable)
        missing_disclosures = self._check_disclosures(text)
        if missing_disclosures:
            issues.extend(missing_disclosures)

        return {
            "compliant": len(issues) == 0,
            "issues": issues,
            "score": 1.0 if len(issues) == 0 else max(0.0, 1.0 - (len(issues) * 0.2)),
        }

    def _check_pii(self, text: str) -> bool:
        """
        Check for potential PII in text
        
        Args:
            text: Text to check
            
        Returns:
            True if PII patterns found
        """
        for pattern in self.pii_patterns:
            if re.search(pattern, text):
                logger.warning("pii_detected", pattern=pattern)
                return True
        return False

    def _check_prohibited(self, text: str) -> bool:
        """
        Check for prohibited phrases
        
        Args:
            text: Text to check
            
        Returns:
            True if prohibited phrases found
        """
        text_lower = text.lower()
        for phrase in self.prohibited_phrases:
            if phrase in text_lower:
                logger.warning("prohibited_phrase_detected", phrase=phrase)
                return True
        return False

    def _check_disclosures(self, text: str) -> List[str]:
        """
        Check for required disclosures
        
        Args:
            text: Text to check
            
        Returns:
            List of missing disclosures
        """
        # This would be customized based on industry requirements
        # For now, return empty list
        return []

    def add_prohibited_phrase(self, phrase: str) -> None:
        """
        Add a prohibited phrase to the list
        
        Args:
            phrase: Phrase to add
        """
        self.prohibited_phrases.append(phrase.lower())

    def add_required_disclosure(self, disclosure: str) -> None:
        """
        Add a required disclosure
        
        Args:
            disclosure: Disclosure text
        """
        self.required_disclosures.append(disclosure)

