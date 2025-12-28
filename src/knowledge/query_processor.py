"""Query processing and enhancement"""

import re
from typing import Dict, Any, Optional, List
from enum import Enum

from openai import OpenAI

from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class QueryIntent(str, Enum):
    """Query intent types"""
    FACTUAL = "factual"  # What is X?
    PROCEDURAL = "procedural"  # How do I X?
    TROUBLESHOOTING = "troubleshooting"  # Why doesn't X work?
    COMPARISON = "comparison"  # What's the difference between X and Y?
    LIST = "list"  # What are the X?
    YES_NO = "yes_no"  # Is X true?
    DEFINITION = "definition"  # Define X
    UNKNOWN = "unknown"


class QueryType(str, Enum):
    """Query type classification"""
    SIMPLE = "simple"
    COMPLEX = "complex"
    MULTI_TURN = "multi_turn"


class QueryProcessor:
    """Process and enhance queries for better retrieval"""

    def __init__(self):
        """Initialize query processor"""
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Intent patterns
        self.intent_patterns = {
            QueryIntent.FACTUAL: [
                r'^what (is|are|was|were)',
                r'^tell me (about|what)',
                r'^explain (what|who|when|where)',
            ],
            QueryIntent.PROCEDURAL: [
                r'^how (do|does|can|should|to)',
                r'^steps? to',
                r'^guide (to|for)',
            ],
            QueryIntent.TROUBLESHOOTING: [
                r'^why (doesn\'t|does|isn\'t|is)',
                r'^what\'s wrong',
                r'^error|problem|issue|bug|fix',
            ],
            QueryIntent.COMPARISON: [
                r'^difference between',
                r'^compare',
                r'^vs\.?|versus',
            ],
            QueryIntent.LIST: [
                r'^list (of|all)',
                r'^what (are|is) (all|the)',
                r'^show me (all|the)',
            ],
            QueryIntent.YES_NO: [
                r'^(is|are|can|does|do|will|should) .+\?$',
                r'^(is|are|can|does|do|will|should) .+$',
            ],
            QueryIntent.DEFINITION: [
                r'^define',
                r'^what (does|is) .+ mean',
            ],
        }

    def process(
        self,
        query: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        use_llm_enhancement: bool = True,
    ) -> Dict[str, Any]:
        """
        Process query with intent classification and enhancement
        
        Args:
            query: User query
            conversation_history: Optional conversation history
            use_llm_enhancement: Whether to use LLM for query enhancement
            
        Returns:
            Dictionary with processed query and metadata
        """
        processed = {
            "original_query": query,
            "processed_query": query,
            "intent": self.classify_intent(query),
            "query_type": self.classify_query_type(query),
            "expanded_queries": [],
            "keywords": self.extract_keywords(query),
        }
        
        # Expand query
        expanded = self.expand_query(query, processed["intent"])
        processed["expanded_queries"] = expanded
        
        # Enhance with conversation context
        if conversation_history:
            processed["processed_query"] = self.add_context(query, conversation_history)
        
        # LLM-based enhancement if enabled
        if use_llm_enhancement:
            try:
                enhanced = self.llm_enhance_query(processed["processed_query"], processed["intent"])
                processed["processed_query"] = enhanced
            except Exception as e:
                logger.warning("llm_enhancement_failed", error=str(e))
        
        return processed

    def classify_intent(self, query: str) -> QueryIntent:
        """Classify query intent"""
        query_lower = query.lower().strip()
        
        # Check patterns
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    return intent
        
        return QueryIntent.UNKNOWN

    def classify_query_type(self, query: str) -> QueryType:
        """Classify query type"""
        # Simple heuristics
        word_count = len(query.split())
        
        if word_count <= 3:
            return QueryType.SIMPLE
        elif word_count > 10:
            return QueryType.COMPLEX
        else:
            return QueryType.SIMPLE

    def extract_keywords(self, query: str) -> List[str]:
        """Extract keywords from query"""
        # Remove stop words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
            "been", "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "should", "could", "may", "might", "must", "can", "this",
            "that", "these", "those", "what", "which", "who", "whom", "whose",
            "where", "when", "why", "how", "all", "each", "every", "some", "any",
        }
        
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords

    def expand_query(self, query: str, intent: QueryIntent) -> List[str]:
        """Expand query with variations"""
        expansions = [query]
        
        # Add variations based on intent
        if intent == QueryIntent.FACTUAL:
            # Add "what is" variations
            if not query.lower().startswith("what"):
                expansions.append(f"what is {query}")
                expansions.append(f"explain {query}")
        
        elif intent == QueryIntent.PROCEDURAL:
            # Add "how to" variations
            if not query.lower().startswith("how"):
                expansions.append(f"how to {query}")
                expansions.append(f"steps to {query}")
        
        elif intent == QueryIntent.TROUBLESHOOTING:
            # Add troubleshooting variations
            expansions.append(f"fix {query}")
            expansions.append(f"solution for {query}")
        
        # Add synonym expansions (simplified)
        synonyms = {
            "error": ["issue", "problem", "bug"],
            "help": ["assist", "support", "guide"],
            "create": ["make", "build", "generate"],
        }
        
        for word, syns in synonyms.items():
            if word in query.lower():
                for syn in syns:
                    expanded = query.lower().replace(word, syn)
                    if expanded != query.lower():
                        expansions.append(expanded)
        
        return list(set(expansions))[:5]  # Limit to 5 expansions

    def add_context(self, query: str, conversation_history: List[Dict[str, Any]]) -> str:
        """Add conversation context to query"""
        if not conversation_history:
            return query
        
        # Get recent context (last 3 exchanges)
        recent = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
        
        # Extract relevant context
        context_parts = []
        for exchange in recent:
            speaker = exchange.get("speaker", "")
            text = exchange.get("text", "")
            if speaker == "customer" and text:
                context_parts.append(text)
        
        if context_parts:
            context = " ".join(context_parts[-2:])  # Last 2 customer messages
            return f"{context} {query}"
        
        return query

    def llm_enhance_query(self, query: str, intent: QueryIntent) -> str:
        """Enhance query using LLM"""
        try:
            prompt = f"""Rewrite the following query to be more effective for information retrieval.
The query intent is: {intent.value}

Original query: {query}

Provide a clearer, more specific version that would help find relevant information.
Return only the enhanced query, nothing else."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a query enhancement assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=100,
            )
            
            enhanced = response.choices[0].message.content.strip()
            return enhanced if enhanced else query
            
        except Exception as e:
            logger.warning("llm_enhancement_error", error=str(e))
            return query

    def rewrite_for_retrieval(self, query: str) -> str:
        """Rewrite query optimized for retrieval"""
        # Remove question words that don't help retrieval
        query = re.sub(r'^(what|who|when|where|why|how)\s+', '', query, flags=re.IGNORECASE)
        
        # Remove punctuation that doesn't help
        query = re.sub(r'[?!]', '', query)
        
        # Normalize whitespace
        query = ' '.join(query.split())
        
        return query.strip()

    def decompose_complex_query(self, query: str) -> List[str]:
        """Decompose complex query into simpler sub-queries"""
        # Simple decomposition based on conjunctions
        conjunctions = [' and ', ' or ', ' but ', ' also ', ' plus ']
        
        sub_queries = [query]
        for conj in conjunctions:
            if conj in query.lower():
                parts = re.split(conj, query, flags=re.IGNORECASE)
                if len(parts) > 1:
                    sub_queries = parts
                    break
        
        return [q.strip() for q in sub_queries if q.strip()]

