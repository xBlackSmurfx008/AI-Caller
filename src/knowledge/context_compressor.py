"""Context compression and summarization system"""

from typing import List, Dict, Any, Optional

from openai import OpenAI

from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ContextCompressor:
    """Compress and summarize context for efficient use"""

    def __init__(self):
        """Initialize context compressor"""
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

    async def compress_context(
        self,
        retrieved_docs: List[Dict[str, Any]],
        query: Optional[str] = None,
        max_length: int = 2000,
        method: str = "summarize",
    ) -> str:
        """
        Compress context from retrieved documents
        
        Args:
            retrieved_docs: Retrieved documents
            query: Optional query for context
            max_length: Maximum length of compressed context
            method: Compression method (summarize, extract, prioritize)
            
        Returns:
            Compressed context string
        """
        if not retrieved_docs:
            return ""
        
        if method == "summarize":
            return await self._summarize_context(retrieved_docs, query, max_length)
        elif method == "extract":
            return self._extract_relevant(retrieved_docs, query, max_length)
        elif method == "prioritize":
            return self._prioritize_chunks(retrieved_docs, query, max_length)
        else:
            return self._prioritize_chunks(retrieved_docs, query, max_length)

    async def _summarize_context(
        self,
        retrieved_docs: List[Dict[str, Any]],
        query: Optional[str] = None,
        max_length: int = 2000,
    ) -> str:
        """Summarize context using LLM"""
        # Combine document contents
        contents = []
        for doc in retrieved_docs[:5]:  # Limit to top 5
            metadata = doc.get("metadata", {})
            content = metadata.get("content", "")
            if not content:
                content = metadata.get("text", "")
            
            title = metadata.get("title", "Document")
            contents.append(f"[{title}]\n{content}")
        
        combined = "\n\n".join(contents)
        
        # Truncate if too long
        if len(combined) > 4000:
            combined = combined[:4000] + "..."
        
        prompt = f"""Summarize the following information{' relevant to the query: ' + query if query else ''}.

Information:
{combined}

Provide a concise summary that captures the key points. Maximum {max_length} characters."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a summarization assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=max_length // 4,  # Rough token estimate
            )
            
            summary = response.choices[0].message.content.strip()
            return summary[:max_length]
            
        except Exception as e:
            logger.warning("context_summarization_error", error=str(e))
            # Fallback to extraction
            return self._extract_relevant(retrieved_docs, query, max_length)

    def _extract_relevant(
        self,
        retrieved_docs: List[Dict[str, Any]],
        query: Optional[str] = None,
        max_length: int = 2000,
    ) -> str:
        """Extract most relevant parts"""
        if not query:
            # Just concatenate top results
            parts = []
            total_length = 0
            
            for doc in retrieved_docs:
                metadata = doc.get("metadata", {})
                content = metadata.get("content", "")
                if not content:
                    content = metadata.get("text", "")
                
                if total_length + len(content) > max_length:
                    remaining = max_length - total_length
                    if remaining > 50:
                        parts.append(content[:remaining])
                    break
                
                parts.append(content)
                total_length += len(content)
            
            return "\n\n".join(parts)
        
        # Extract relevant sentences
        query_terms = query.lower().split()
        relevant_parts = []
        total_length = 0
        
        for doc in retrieved_docs:
            metadata = doc.get("metadata", {})
            content = metadata.get("content", "")
            if not content:
                content = metadata.get("text", "")
            
            # Find sentences with query terms
            sentences = content.split('.')
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if any(term in sentence_lower for term in query_terms):
                    if total_length + len(sentence) > max_length:
                        return "\n".join(relevant_parts)
                    
                    relevant_parts.append(sentence.strip())
                    total_length += len(sentence)
        
        return "\n".join(relevant_parts) if relevant_parts else ""

    def _prioritize_chunks(
        self,
        retrieved_docs: List[Dict[str, Any]],
        query: Optional[str] = None,
        max_length: int = 2000,
    ) -> str:
        """Prioritize chunks by relevance score"""
        # Sort by score
        sorted_docs = sorted(
            retrieved_docs,
            key=lambda x: x.get("score", 0.0),
            reverse=True
        )
        
        parts = []
        total_length = 0
        
        for doc in sorted_docs:
            metadata = doc.get("metadata", {})
            content = metadata.get("content", "")
            if not content:
                content = metadata.get("text", "")
            
            title = metadata.get("title", "Document")
            
            formatted = f"[{title}]\n{content}"
            
            if total_length + len(formatted) > max_length:
                remaining = max_length - total_length
                if remaining > 50:
                    parts.append(formatted[:remaining])
                break
            
            parts.append(formatted)
            total_length += len(formatted)
        
        return "\n\n".join(parts)

    def remove_redundancy(self, context: str) -> str:
        """Remove redundant information from context"""
        sentences = context.split('.')
        unique_sentences = []
        seen = set()
        
        for sentence in sentences:
            sentence_stripped = sentence.strip()
            if not sentence_stripped:
                continue
            
            # Simple deduplication
            sentence_lower = sentence_stripped.lower()
            if sentence_lower not in seen:
                seen.add(sentence_lower)
                unique_sentences.append(sentence_stripped)
        
        return '. '.join(unique_sentences)

    def maintain_coherence(self, context: str) -> str:
        """Maintain context coherence"""
        # Simple coherence check: ensure sentences flow
        sentences = context.split('.')
        
        # Remove very short sentences that break flow
        filtered = [s.strip() for s in sentences if len(s.strip()) > 10]
        
        return '. '.join(filtered)

