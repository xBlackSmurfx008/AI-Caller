"""Hybrid search combining semantic, keyword, and metadata filtering"""

from typing import List, Dict, Any, Optional
import math

from src.knowledge.vector_store import VectorStore, get_vector_store
from src.knowledge.embeddings import EmbeddingManager
from src.utils.logging import get_logger

logger = get_logger(__name__)


class BM25Scorer:
    """Simple BM25 keyword scoring implementation"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 scorer
        
        Args:
            k1: Term frequency saturation parameter
            b: Length normalization parameter
        """
        self.k1 = k1
        self.b = b

    def score(
        self,
        query_terms: List[str],
        document_terms: List[str],
        document_length: int,
        average_document_length: float,
    ) -> float:
        """
        Calculate BM25 score
        
        Args:
            query_terms: Query terms
            document_terms: Document terms
            document_length: Document length
            average_document_length: Average document length in collection
            
        Returns:
            BM25 score
        """
        score = 0.0
        
        # Term frequency in document
        term_freqs = {}
        for term in document_terms:
            term_freqs[term] = term_freqs.get(term, 0) + 1
        
        # Calculate score for each query term
        for term in query_terms:
            if term not in term_freqs:
                continue
            
            tf = term_freqs[term]
            
            # BM25 formula
            idf = math.log((len(document_terms) + 1) / (term_freqs[term] + 1) + 1)
            length_norm = (1 - self.b + self.b * (document_length / average_document_length))
            term_score = idf * (tf * (self.k1 + 1)) / (tf + self.k1 * length_norm)
            
            score += term_score
        
        return score


class HybridSearch:
    """Hybrid search combining semantic and keyword search"""

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        embedding_manager: Optional[EmbeddingManager] = None,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
    ):
        """
        Initialize hybrid search
        
        Args:
            vector_store: Vector store instance
            embedding_manager: Embedding manager instance
            semantic_weight: Weight for semantic search (0-1)
            keyword_weight: Weight for keyword search (0-1)
        """
        self.vector_store = vector_store or get_vector_store()
        self.embedding_manager = embedding_manager or EmbeddingManager()
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        self.bm25_scorer = BM25Scorer()
        
        # Normalize weights
        total_weight = semantic_weight + keyword_weight
        if total_weight > 0:
            self.semantic_weight = semantic_weight / total_weight
            self.keyword_weight = keyword_weight / total_weight

    async def search(
        self,
        query: str,
        top_k: int = 10,
        namespace: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
        query_terms: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search
        
        Args:
            query: Search query
            top_k: Number of results to return
            namespace: Optional namespace
            metadata_filter: Optional metadata filter
            query_terms: Optional pre-extracted query terms
            
        Returns:
            List of search results with scores
        """
        # Extract query terms if not provided
        if query_terms is None:
            query_terms = self._extract_terms(query)
        
        # Semantic search
        semantic_results = await self._semantic_search(
            query=query,
            top_k=top_k * 2,  # Get more for reranking
            namespace=namespace,
            filter=metadata_filter,
        )
        
        # Keyword search
        keyword_results = await self._keyword_search(
            query_terms=query_terms,
            top_k=top_k * 2,
            namespace=namespace,
            metadata_filter=metadata_filter,
        )
        
        # Combine and rerank
        combined_results = self._combine_results(
            semantic_results=semantic_results,
            keyword_results=keyword_results,
            query_terms=query_terms,
        )
        
        # Apply metadata filtering
        if metadata_filter:
            combined_results = self._apply_metadata_filter(combined_results, metadata_filter)
        
        # Return top k
        return combined_results[:top_k]

    async def _semantic_search(
        self,
        query: str,
        top_k: int,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform semantic vector search"""
        try:
            # Generate query embedding
            query_embedding = (await self.embedding_manager.embed([query]))[0]
            
            # Search vector store
            await self.vector_store.initialize()
            results = await self.vector_store.query(
                query_vector=query_embedding,
                top_k=top_k,
                namespace=namespace,
                filter=filter,
            )
            
            return results
            
        except Exception as e:
            logger.error("semantic_search_error", error=str(e))
            return []

    async def _keyword_search(
        self,
        query_terms: List[str],
        top_k: int,
        namespace: Optional[str] = None,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Perform keyword-based search"""
        # For now, we'll use a simplified approach
        # In production, you'd want to use Elasticsearch or similar
        
        # Get all documents from vector store (simplified - in production use inverted index)
        # This is a placeholder - actual implementation would use an inverted index
        
        # For now, return empty results and rely on semantic search
        # A full implementation would:
        # 1. Build inverted index during document ingestion
        # 2. Use BM25 scoring on indexed documents
        # 3. Return keyword-matched documents
        
        return []

    def _combine_results(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        query_terms: List[str],
    ) -> List[Dict[str, Any]]:
        """Combine semantic and keyword results with weighted scoring"""
        # Create result map by ID
        result_map = {}
        
        # Add semantic results
        for result in semantic_results:
            result_id = result.get("id")
            if result_id:
                result_map[result_id] = {
                    **result,
                    "semantic_score": result.get("score", 0.0),
                    "keyword_score": 0.0,
                    "combined_score": 0.0,
                }
        
        # Add keyword results and calculate keyword scores
        for result in keyword_results:
            result_id = result.get("id")
            if result_id:
                if result_id in result_map:
                    # Calculate keyword score
                    content = result.get("metadata", {}).get("content", "")
                    if not content:
                        content = result.get("metadata", {}).get("text", "")
                    
                    keyword_score = self._calculate_keyword_score(content, query_terms)
                    result_map[result_id]["keyword_score"] = keyword_score
                else:
                    result_map[result_id] = {
                        **result,
                        "semantic_score": 0.0,
                        "keyword_score": result.get("score", 0.0),
                        "combined_score": 0.0,
                    }
        
        # Calculate combined scores
        for result_id, result in result_map.items():
            semantic_score = result.get("semantic_score", 0.0)
            keyword_score = result.get("keyword_score", 0.0)
            
            # Normalize scores to 0-1 range
            semantic_norm = min(semantic_score, 1.0) if semantic_score <= 1.0 else semantic_score / 2.0
            keyword_norm = min(keyword_score, 1.0) if keyword_score <= 1.0 else keyword_score / 10.0
            
            # Weighted combination
            combined_score = (
                self.semantic_weight * semantic_norm +
                self.keyword_weight * keyword_norm
            )
            
            result["combined_score"] = combined_score
            result["score"] = combined_score  # Update main score
        
        # Sort by combined score
        sorted_results = sorted(
            result_map.values(),
            key=lambda x: x.get("combined_score", 0.0),
            reverse=True
        )
        
        return sorted_results

    def _calculate_keyword_score(self, content: str, query_terms: List[str]) -> float:
        """Calculate keyword match score"""
        if not content or not query_terms:
            return 0.0
        
        content_lower = content.lower()
        content_terms = content_lower.split()
        
        # Count matches
        matches = sum(1 for term in query_terms if term.lower() in content_lower)
        
        # Calculate score
        if matches == 0:
            return 0.0
        
        # Simple TF-based score
        score = matches / len(query_terms)
        
        # Boost for exact phrase matches
        query_phrase = " ".join(query_terms).lower()
        if query_phrase in content_lower:
            score *= 1.5
        
        return min(score, 1.0)

    def _extract_terms(self, query: str) -> List[str]:
        """Extract search terms from query"""
        import re
        
        # Remove punctuation and split
        terms = re.findall(r'\b\w+\b', query.lower())
        
        # Remove stop words
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "are", "was", "were", "be",
            "been", "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "should", "could", "may", "might", "must", "can",
        }
        
        terms = [t for t in terms if t not in stop_words and len(t) > 2]
        
        return terms

    def _apply_metadata_filter(
        self,
        results: List[Dict[str, Any]],
        metadata_filter: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Apply metadata filtering to results"""
        filtered = []
        
        for result in results:
            metadata = result.get("metadata", {})
            match = True
            
            for key, value in metadata_filter.items():
                if key not in metadata:
                    match = False
                    break
                
                # Handle different filter types
                if isinstance(value, dict):
                    # Range or comparison filters
                    if "$gte" in value:
                        if metadata[key] < value["$gte"]:
                            match = False
                            break
                    if "$lte" in value:
                        if metadata[key] > value["$lte"]:
                            match = False
                            break
                elif isinstance(value, list):
                    # In filter
                    if metadata[key] not in value:
                        match = False
                        break
                else:
                    # Exact match
                    if metadata[key] != value:
                        match = False
                        break
            
            if match:
                filtered.append(result)
        
        return filtered

    async def faceted_search(
        self,
        query: str,
        facets: List[str],
        top_k: int = 10,
        namespace: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Perform faceted search
        
        Args:
            query: Search query
            facets: List of facet fields
            top_k: Number of results per facet
            namespace: Optional namespace
            
        Returns:
            Dictionary with facets and results
        """
        # Get base results
        results = await self.search(query, top_k=top_k * 2, namespace=namespace)
        
        # Group by facets
        facet_results = {}
        for facet in facets:
            facet_values = {}
            for result in results:
                metadata = result.get("metadata", {})
                facet_value = metadata.get(facet, "unknown")
                if facet_value not in facet_values:
                    facet_values[facet_value] = []
                facet_values[facet_value].append(result)
            
            facet_results[facet] = facet_values
        
        return {
            "results": results[:top_k],
            "facets": facet_results,
        }

