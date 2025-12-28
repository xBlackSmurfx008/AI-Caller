"""Reranking system with cross-encoder scoring"""

from typing import List, Dict, Any, Optional
import hashlib

from openai import OpenAI

from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class Reranker:
    """Rerank search results using cross-encoder and diversity"""

    def __init__(self, use_cross_encoder: bool = True):
        """
        Initialize reranker
        
        Args:
            use_cross_encoder: Whether to use cross-encoder for reranking
        """
        self.use_cross_encoder = use_cross_encoder
        if use_cross_encoder:
            self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

    async def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: Optional[int] = None,
        diversity_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        Rerank search results
        
        Args:
            query: Search query
            results: Initial search results
            top_k: Number of results to return
            diversity_threshold: Threshold for diversity filtering
            
        Returns:
            Reranked results
        """
        if not results:
            return []
        
        # Deduplicate results
        results = self._deduplicate(results)
        
        # Calculate relevance scores
        scored_results = await self._score_relevance(query, results)
        
        # Apply diversity
        diverse_results = self._apply_diversity(scored_results, diversity_threshold)
        
        # Normalize scores
        normalized_results = self._normalize_scores(diverse_results)
        
        # Sort by final score
        sorted_results = sorted(
            normalized_results,
            key=lambda x: x.get("final_score", 0.0),
            reverse=True
        )
        
        # Return top k
        if top_k:
            return sorted_results[:top_k]
        
        return sorted_results

    async def _score_relevance(
        self,
        query: str,
        results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Score relevance of results"""
        scored = []
        
        for result in results:
            content = result.get("metadata", {}).get("content", "")
            if not content:
                content = result.get("metadata", {}).get("text", "")
            
            # Get original score
            original_score = result.get("score", 0.0)
            
            # Cross-encoder score if enabled
            if self.use_cross_encoder:
                cross_score = await self._cross_encoder_score(query, content)
            else:
                cross_score = original_score
            
            # Combine scores
            # Weight: 60% cross-encoder, 40% original
            final_score = 0.6 * cross_score + 0.4 * original_score
            
            scored.append({
                **result,
                "original_score": original_score,
                "cross_encoder_score": cross_score,
                "final_score": final_score,
            })
        
        return scored

    async def _cross_encoder_score(self, query: str, content: str) -> float:
        """
        Calculate cross-encoder relevance score
        
        Args:
            query: Search query
            content: Document content
            
        Returns:
            Relevance score between 0 and 1
        """
        if not content:
            return 0.0
        
        # Truncate content for efficiency
        max_content_length = 500
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."
        
        try:
            prompt = f"""Rate the relevance of the following document content to the query on a scale of 0.0 to 1.0.

Query: {query}

Document Content:
{content}

Respond with only a number between 0.0 and 1.0 representing the relevance score."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a relevance scoring assistant. Respond only with a number between 0.0 and 1.0."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=10,
            )
            
            score_str = response.choices[0].message.content.strip()
            score = float(score_str)
            
            # Ensure score is in valid range
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.warning("cross_encoder_scoring_failed", error=str(e))
            # Fallback to simple keyword matching
            return self._simple_relevance_score(query, content)

    def _simple_relevance_score(self, query: str, content: str) -> float:
        """Simple relevance scoring fallback"""
        if not query or not content:
            return 0.0
        
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Count query term matches
        query_terms = query_lower.split()
        matches = sum(1 for term in query_terms if term in content_lower)
        
        if matches == 0:
            return 0.0
        
        # Calculate score
        score = matches / len(query_terms)
        
        # Boost for exact phrase match
        if query_lower in content_lower:
            score = min(score * 1.5, 1.0)
        
        return score

    def _deduplicate(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results"""
        seen = set()
        deduplicated = []
        
        for result in results:
            # Create hash of content for deduplication
            content = result.get("metadata", {}).get("content", "")
            if not content:
                content = result.get("metadata", {}).get("text", "")
            
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            if content_hash not in seen:
                seen.add(content_hash)
                deduplicated.append(result)
        
        return deduplicated

    def _apply_diversity(
        self,
        results: List[Dict[str, Any]],
        threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        Apply diversity to results to avoid redundancy
        
        Args:
            results: Scored results
            threshold: Similarity threshold for diversity
            
        Returns:
            Diverse results
        """
        if len(results) <= 1:
            return results
        
        diverse = [results[0]]  # Always include top result
        
        for result in results[1:]:
            # Check similarity with already selected results
            is_diverse = True
            
            for selected in diverse:
                similarity = self._calculate_similarity(result, selected)
                if similarity > threshold:
                    is_diverse = False
                    break
            
            if is_diverse:
                diverse.append(result)
        
        return diverse

    def _calculate_similarity(
        self,
        result1: Dict[str, Any],
        result2: Dict[str, Any],
    ) -> float:
        """Calculate similarity between two results"""
        # Simple similarity based on content overlap
        content1 = result1.get("metadata", {}).get("content", "")
        content2 = result2.get("metadata", {}).get("content", "")
        
        if not content1 or not content2:
            return 0.0
        
        # Extract words
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        if union == 0:
            return 0.0
        
        return intersection / union

    def _normalize_scores(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize scores to 0-1 range"""
        if not results:
            return results
        
        scores = [r.get("final_score", 0.0) for r in results]
        
        if not scores:
            return results
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            # All scores are the same
            return results
        
        # Normalize
        normalized = []
        for result in results:
            score = result.get("final_score", 0.0)
            normalized_score = (score - min_score) / (max_score - min_score)
            
            normalized.append({
                **result,
                "final_score": normalized_score,
                "normalized_score": normalized_score,
            })
        
        return normalized

    def rerank_with_confidence(
        self,
        query: str,
        results: List[Dict[str, Any]],
        min_confidence: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """
        Rerank results and filter by confidence
        
        Args:
            query: Search query
            results: Search results
            min_confidence: Minimum confidence threshold
            
        Returns:
            Filtered and reranked results
        """
        reranked = await self.rerank(query, results)
        
        # Filter by confidence
        filtered = [
            r for r in reranked
            if r.get("final_score", 0.0) >= min_confidence
        ]
        
        return filtered

