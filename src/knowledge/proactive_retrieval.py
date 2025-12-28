"""Proactive knowledge retrieval for predictive assistance"""

from typing import List, Dict, Any, Optional
from collections import deque

from openai import OpenAI

from src.knowledge.hybrid_search import HybridSearch
from src.knowledge.query_processor import QueryProcessor
from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ProactiveRetrieval:
    """Proactive knowledge retrieval based on conversation context"""

    def __init__(
        self,
        hybrid_search: Optional[HybridSearch] = None,
        query_processor: Optional[QueryProcessor] = None,
    ):
        """
        Initialize proactive retrieval
        
        Args:
            hybrid_search: Hybrid search instance
            query_processor: Query processor instance
        """
        self.hybrid_search = hybrid_search or HybridSearch()
        self.query_processor = query_processor or QueryProcessor()
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Conversation history buffer
        self.conversation_buffer: deque = deque(maxlen=10)

    def predict_next_queries(
        self,
        conversation_history: List[Dict[str, Any]],
        max_predictions: int = 3,
    ) -> List[str]:
        """
        Predict likely next queries based on conversation
        
        Args:
            conversation_history: Conversation history
            max_predictions: Maximum number of predictions
            
        Returns:
            List of predicted queries
        """
        if not conversation_history:
            return []
        
        # Get recent context
        recent_context = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
        
        # Extract key topics
        topics = self._extract_topics(recent_context)
        
        # Generate predicted queries
        try:
            predicted = self._generate_predictions(topics, max_predictions)
            return predicted
        except Exception as e:
            logger.warning("query_prediction_failed", error=str(e))
            return []

    def _extract_topics(self, conversation: List[Dict[str, Any]]) -> List[str]:
        """Extract key topics from conversation"""
        topics = []
        
        for exchange in conversation:
            text = exchange.get("text", "")
            speaker = exchange.get("speaker", "")
            
            if speaker == "customer" and text:
                # Extract nouns and important terms
                words = text.lower().split()
                # Simple keyword extraction
                keywords = [w for w in words if len(w) > 4 and w not in {
                    "what", "where", "when", "which", "about", "there", "their"
                }]
                topics.extend(keywords[:3])  # Top 3 keywords per message
        
        return list(set(topics))[:5]  # Unique topics, max 5

    def _generate_predictions(self, topics: List[str], max_predictions: int) -> List[str]:
        """Generate predicted queries using LLM"""
        if not topics:
            return []
        
        topics_str = ", ".join(topics)
        
        prompt = f"""Based on these conversation topics: {topics_str}

Generate {max_predictions} likely follow-up questions the user might ask.
Make them specific and relevant to the topics.
Return one question per line."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a query prediction assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=150,
            )
            
            predictions = response.choices[0].message.content.strip().split('\n')
            predictions = [p.strip() for p in predictions if p.strip()]
            
            return predictions[:max_predictions]
            
        except Exception as e:
            logger.error("prediction_generation_error", error=str(e))
            return []

    async def prefetch_knowledge(
        self,
        predicted_queries: List[str],
        namespace: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Prefetch knowledge for predicted queries
        
        Args:
            predicted_queries: List of predicted queries
            namespace: Optional namespace
            
        Returns:
            Dictionary mapping queries to retrieved results
        """
        prefetched = {}
        
        for query in predicted_queries:
            try:
                results = await self.hybrid_search.search(
                    query=query,
                    top_k=3,  # Fewer results for prefetching
                    namespace=namespace,
                )
                prefetched[query] = results
            except Exception as e:
                logger.warning("prefetch_error", query=query[:50], error=str(e))
                prefetched[query] = []
        
        return prefetched

    def suggest_knowledge_hints(
        self,
        conversation_history: List[Dict[str, Any]],
        current_query: str,
    ) -> List[str]:
        """
        Suggest knowledge hints during conversation
        
        Args:
            conversation_history: Conversation history
            current_query: Current user query
            
        Returns:
            List of knowledge hints/suggestions
        """
        hints = []
        
        # Analyze current query
        processed = self.query_processor.process(current_query, conversation_history)
        intent = processed.get("intent")
        
        # Generate hints based on intent
        if intent == "troubleshooting":
            hints.append("I can help troubleshoot this issue. Would you like me to search for solutions?")
        elif intent == "procedural":
            hints.append("I can provide step-by-step instructions for this.")
        elif intent == "factual":
            hints.append("Let me find the most up-to-date information about this.")
        
        return hints

    def update_conversation_buffer(self, exchange: Dict[str, Any]) -> None:
        """Update conversation buffer"""
        self.conversation_buffer.append(exchange)

    async def get_contextual_suggestions(
        self,
        current_query: str,
        namespace: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get contextual knowledge suggestions
        
        Args:
            current_query: Current query
            namespace: Optional namespace
            
        Returns:
            List of suggested knowledge items
        """
        # Use conversation buffer for context
        conversation_history = list(self.conversation_buffer)
        
        # Predict next queries
        predicted = self.predict_next_queries(conversation_history)
        
        # Prefetch knowledge
        prefetched = await self.prefetch_knowledge(predicted, namespace)
        
        # Format as suggestions
        suggestions = []
        for query, results in prefetched.items():
            if results:
                top_result = results[0]
                suggestions.append({
                    "query": query,
                    "title": top_result.get("metadata", {}).get("title", ""),
                    "snippet": top_result.get("metadata", {}).get("content", "")[:100],
                    "relevance": top_result.get("score", 0.0),
                })
        
        return suggestions

