"""Intent classification for queries"""

from typing import Dict, Any, Optional
from enum import Enum

from openai import OpenAI

from src.knowledge.query_processor import QueryIntent
from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class IntentClassifier:
    """Classify query intent using patterns and LLM"""

    def __init__(self, use_llm: bool = False):
        """
        Initialize intent classifier
        
        Args:
            use_llm: Whether to use LLM for classification
        """
        self.use_llm = use_llm
        if use_llm:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def classify(
        self,
        query: str,
        conversation_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Classify query intent
        
        Args:
            query: User query
            conversation_context: Optional conversation context
            
        Returns:
            Dictionary with intent classification and confidence
        """
        # Pattern-based classification
        pattern_intent = self._classify_by_patterns(query)
        
        if self.use_llm:
            # LLM-based classification for better accuracy
            try:
                llm_intent = self._classify_with_llm(query, conversation_context)
                # Combine both results
                if llm_intent["confidence"] > pattern_intent["confidence"]:
                    return llm_intent
            except Exception as e:
                logger.warning("llm_intent_classification_failed", error=str(e))
        
        return pattern_intent

    def _classify_by_patterns(self, query: str) -> Dict[str, Any]:
        """Classify intent using pattern matching"""
        from src.knowledge.query_processor import QueryProcessor
        
        processor = QueryProcessor()
        intent = processor.classify_intent(query)
        
        # Calculate confidence based on pattern match strength
        confidence = 0.7 if intent != QueryIntent.UNKNOWN else 0.3
        
        return {
            "intent": intent.value,
            "confidence": confidence,
            "method": "pattern",
        }

    def _classify_with_llm(self, query: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Classify intent using LLM"""
        prompt = f"""Classify the intent of the following query into one of these categories:
- factual: Asking for facts or information
- procedural: Asking how to do something
- troubleshooting: Asking about problems or errors
- comparison: Comparing two or more things
- list: Asking for a list of items
- yes_no: Yes/no question
- definition: Asking for a definition

Query: {query}
{f'Context: {context}' if context else ''}

Respond with only the intent category name."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an intent classification assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=20,
            )
            
            intent_str = response.choices[0].message.content.strip().lower()
            
            # Map to QueryIntent enum
            intent_map = {
                "factual": QueryIntent.FACTUAL,
                "procedural": QueryIntent.PROCEDURAL,
                "troubleshooting": QueryIntent.TROUBLESHOOTING,
                "comparison": QueryIntent.COMPARISON,
                "list": QueryIntent.LIST,
                "yes_no": QueryIntent.YES_NO,
                "definition": QueryIntent.DEFINITION,
            }
            
            intent = intent_map.get(intent_str, QueryIntent.UNKNOWN)
            
            return {
                "intent": intent.value,
                "confidence": 0.9,
                "method": "llm",
            }
            
        except Exception as e:
            logger.error("llm_classification_error", error=str(e))
            return self._classify_by_patterns(query)

