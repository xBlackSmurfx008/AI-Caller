"""Multi-step reasoning RAG with iterative retrieval"""

from typing import List, Dict, Any, Optional

from openai import OpenAI

from src.knowledge.hybrid_search import HybridSearch
from src.knowledge.query_processor import QueryProcessor
from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class MultiStepRAG:
    """Multi-step reasoning RAG with iterative refinement"""

    def __init__(
        self,
        hybrid_search: Optional[HybridSearch] = None,
        query_processor: Optional[QueryProcessor] = None,
        max_iterations: int = 3,
    ):
        """
        Initialize multi-step RAG
        
        Args:
            hybrid_search: Hybrid search instance
            query_processor: Query processor instance
            max_iterations: Maximum iterations for refinement
        """
        self.hybrid_search = hybrid_search or HybridSearch()
        self.query_processor = query_processor or QueryProcessor()
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.max_iterations = max_iterations

    async def retrieve_with_reasoning(
        self,
        query: str,
        namespace: Optional[str] = None,
        initial_results: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve with multi-step reasoning
        
        Args:
            query: User query
            namespace: Optional namespace
            initial_results: Optional initial results
            
        Returns:
            Dictionary with final results and reasoning chain
        """
        reasoning_chain = []
        current_query = query
        all_results = []
        
        # Initial retrieval
        if initial_results:
            results = initial_results
        else:
            results = await self.hybrid_search.search(
                query=current_query,
                top_k=5,
                namespace=namespace,
            )
        
        all_results.extend(results)
        reasoning_chain.append({
            "step": 1,
            "query": current_query,
            "results_count": len(results),
            "top_score": results[0].get("score") if results else None,
        })
        
        # Iterative refinement
        for iteration in range(2, self.max_iterations + 1):
            # Analyze if we need to refine
            should_refine = self._should_refine(query, results)
            
            if not should_refine:
                break
            
            # Generate refined query
            refined_query = await self._refine_query(query, results, reasoning_chain)
            
            if not refined_query or refined_query == current_query:
                break
            
            # Retrieve with refined query
            refined_results = await self.hybrid_search.search(
                query=refined_query,
                top_k=5,
                namespace=namespace,
            )
            
            # Merge results
            results = self._merge_results(results, refined_results)
            all_results.extend(refined_results)
            
            reasoning_chain.append({
                "step": iteration,
                "query": refined_query,
                "results_count": len(refined_results),
                "top_score": refined_results[0].get("score") if refined_results else None,
            })
            
            current_query = refined_query
        
        # Verify facts
        verified_results = await self._verify_facts(query, results)
        
        return {
            "results": verified_results,
            "reasoning_chain": reasoning_chain,
            "iterations": len(reasoning_chain),
            "all_results": all_results,
        }

    def _should_refine(self, original_query: str, results: List[Dict[str, Any]]) -> bool:
        """Determine if query should be refined"""
        if not results:
            return True
        
        # Check if top result has high confidence
        top_score = results[0].get("score", 0.0)
        if top_score > 0.8:
            return False
        
        # Check if query is complex (multiple parts)
        query_parts = original_query.lower().split()
        if len(query_parts) > 8:
            return True
        
        return False

    async def _refine_query(
        self,
        original_query: str,
        current_results: List[Dict[str, Any]],
        reasoning_chain: List[Dict[str, Any]],
    ) -> str:
        """Refine query based on current results"""
        # Extract key information from results
        result_summaries = []
        for result in current_results[:3]:
            content = result.get("metadata", {}).get("content", "")
            if content:
                result_summaries.append(content[:200])
        
        prompt = f"""Original query: {original_query}

Current results summary:
{chr(10).join(f"- {summary}" for summary in result_summaries)}

Previous reasoning steps:
{chr(10).join(f"Step {step['step']}: {step['query']}" for step in reasoning_chain)}

Generate a refined query that will help find more specific or complementary information.
Return only the refined query, nothing else."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a query refinement assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=100,
            )
            
            refined = response.choices[0].message.content.strip()
            return refined if refined else original_query
            
        except Exception as e:
            logger.warning("query_refinement_error", error=str(e))
            return original_query

    def _merge_results(
        self,
        results1: List[Dict[str, Any]],
        results2: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Merge and deduplicate results"""
        # Create result map by ID
        result_map = {}
        
        for result in results1 + results2:
            result_id = result.get("id")
            if result_id:
                if result_id not in result_map:
                    result_map[result_id] = result
                else:
                    # Keep higher scoring version
                    if result.get("score", 0.0) > result_map[result_id].get("score", 0.0):
                        result_map[result_id] = result
        
        # Sort by score
        merged = sorted(
            result_map.values(),
            key=lambda x: x.get("score", 0.0),
            reverse=True
        )
        
        return merged[:10]  # Return top 10

    async def _verify_facts(
        self,
        query: str,
        results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Verify facts in retrieved results"""
        verified = []
        
        for result in results:
            content = result.get("metadata", {}).get("content", "")
            if not content:
                verified.append(result)
                continue
            
            # Simple verification: check if content is relevant to query
            relevance = self._check_relevance(query, content)
            
            verified_result = {
                **result,
                "verified": relevance > 0.5,
                "verification_score": relevance,
            }
            
            verified.append(verified_result)
        
        # Sort by verification score
        verified.sort(key=lambda x: x.get("verification_score", 0.0), reverse=True)
        
        return verified

    def _check_relevance(self, query: str, content: str) -> float:
        """Check relevance of content to query"""
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Count query term matches
        query_terms = query_lower.split()
        matches = sum(1 for term in query_terms if term in content_lower)
        
        if matches == 0:
            return 0.0
        
        return min(matches / len(query_terms), 1.0)

    async def decompose_complex_query(self, query: str) -> List[str]:
        """Decompose complex query into sub-queries"""
        prompt = f"""Decompose the following complex query into simpler sub-queries that can be answered independently.

Query: {query}

Return each sub-query on a new line. Return only the sub-queries, nothing else."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a query decomposition assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200,
            )
            
            sub_queries = response.choices[0].message.content.strip().split('\n')
            return [q.strip() for q in sub_queries if q.strip()]
            
        except Exception as e:
            logger.warning("query_decomposition_error", error=str(e))
            # Fallback: simple split
            return [query]

