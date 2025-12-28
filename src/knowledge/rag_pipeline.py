"""RAG (Retrieval-Augmented Generation) pipeline"""

from typing import List, Dict, Any, Optional

from openai import OpenAI

from src.knowledge.vector_store import get_vector_store, VectorStore
from src.utils.config import get_settings
from src.utils.errors import KnowledgeBaseError
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class RAGPipeline:
    """RAG pipeline for knowledge retrieval and context injection"""

    def __init__(self, business_id: Optional[str] = None):
        """
        Initialize RAG pipeline
        
        Args:
            business_id: Business configuration ID for namespace isolation
        """
        self.business_id = business_id
        self.vector_store = get_vector_store()
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.top_k = 5
        self.similarity_threshold = 0.7

    async def initialize(self) -> None:
        """Initialize vector store"""
        await self.vector_store.initialize()

    async def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter: Optional[Dict[str, Any]] = None,
        vendor: Optional[str] = None,
        doc_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant knowledge from vector store
        
        Args:
            query: Query text
            top_k: Number of results to return
            filter: Optional metadata filter
            vendor: Optional vendor filter (openai, twilio, etc.)
            doc_type: Optional document type filter (api_reference, guide, etc.)
            
        Returns:
            List of retrieved documents with metadata
        """
        try:
            # Build filter with vendor and doc_type if provided
            combined_filter = filter or {}
            if vendor:
                combined_filter["vendor"] = vendor
            if doc_type:
                combined_filter["doc_type"] = doc_type
            
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)

            # Query vector store
            top_k = top_k or self.top_k
            results = await self.vector_store.query(
                query_vector=query_embedding,
                top_k=top_k,
                namespace=self.business_id,
                filter=combined_filter if combined_filter else None,
            )

            # Filter by similarity threshold
            filtered_results = [
                result for result in results
                if result.get("score", 0) >= self.similarity_threshold
            ]
            
            # If vendor specified but no results, try without vendor filter
            if vendor and not filtered_results:
                logger.debug("no_results_with_vendor", vendor=vendor, query=query[:50])
                # Retry without vendor filter but prioritize vendor in results
                results = await self.vector_store.query(
                    query_vector=query_embedding,
                    top_k=top_k * 2,  # Get more results to filter
                    namespace=self.business_id,
                    filter=filter,
                )
                # Prioritize vendor results
                vendor_results = [r for r in results if r.get("metadata", {}).get("vendor") == vendor]
                other_results = [r for r in results if r.get("metadata", {}).get("vendor") != vendor]
                filtered_results = (vendor_results + other_results)[:top_k]

            logger.debug(
                "rag_retrieval",
                query=query[:50],
                results=len(filtered_results),
                vendor=vendor,
                doc_type=doc_type,
                top_score=filtered_results[0].get("score") if filtered_results else None,
            )

            return filtered_results

        except Exception as e:
            logger.error("rag_retrieval_error", error=str(e), query=query[:50])
            raise KnowledgeBaseError(f"Failed to retrieve knowledge: {str(e)}") from e

    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )

            return response.data[0].embedding

        except Exception as e:
            logger.error("embedding_generation_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to generate embedding: {str(e)}") from e

    def format_context(
        self,
        retrieved_docs: List[Dict[str, Any]],
        max_length: int = 2000,
        include_source: bool = True,
    ) -> str:
        """
        Format retrieved documents into context string
        
        Args:
            retrieved_docs: List of retrieved documents
            max_length: Maximum context length in characters
            include_source: Whether to include source URLs
            
        Returns:
            Formatted context string
        """
        if not retrieved_docs:
            return ""

        context_parts = []
        total_length = 0

        for doc in retrieved_docs:
            metadata = doc.get("metadata", {})
            content = metadata.get("content", "")
            title = metadata.get("title", "Unknown")
            vendor = metadata.get("vendor", "")
            doc_type = metadata.get("doc_type", "")
            source = metadata.get("source", "")
            
            # Format with vendor and doc type info
            header = f"[{title}]"
            if vendor:
                header += f" ({vendor.upper()})"
            if doc_type:
                header += f" - {doc_type.replace('_', ' ').title()}"
            
            formatted = f"{header}\n{content}\n"
            
            # Add source URL if available
            if include_source and source and source.startswith("http"):
                formatted += f"Source: {source}\n"
            
            formatted += "\n"

            if total_length + len(formatted) > max_length:
                break

            context_parts.append(formatted)
            total_length += len(formatted)

        return "\n".join(context_parts).strip()

    def inject_context(
        self,
        system_prompt: str,
        context: str,
        query: Optional[str] = None,
        is_documentation: bool = False,
    ) -> str:
        """
        Inject retrieved context into system prompt
        
        Args:
            system_prompt: Original system prompt
            context: Retrieved context
            query: Optional current query
            is_documentation: Whether this is documentation context
            
        Returns:
            Enhanced system prompt with context
        """
        if not context:
            return system_prompt

        if is_documentation:
            context_section = f"""
## Documentation Reference

The following documentation is available:

{context}

Use this documentation to provide accurate technical information. Include code examples when relevant. Cite sources when possible.
"""
        else:
            context_section = f"""
## Knowledge Base Context

The following information is available from the knowledge base:

{context}

Use this information to provide accurate and helpful responses. If the information doesn't answer the question, say so and offer to help in other ways.
"""

        # Append context to system prompt
        enhanced_prompt = f"{system_prompt}\n\n{context_section}"

        if query:
            enhanced_prompt += f"\n\nCurrent question: {query}"

        return enhanced_prompt

    async def query_with_context(
        self,
        query: str,
        system_prompt: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        top_k: Optional[int] = None,
        vendor: Optional[str] = None,
        doc_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Complete RAG pipeline: retrieve, format, and prepare for generation
        
        Args:
            query: User query
            system_prompt: System prompt
            conversation_history: Optional conversation history
            top_k: Number of documents to retrieve
            vendor: Optional vendor filter
            doc_type: Optional document type filter
            
        Returns:
            Dictionary with enhanced prompt and retrieved context
        """
        try:
            # Retrieve relevant knowledge
            retrieved_docs = await self.retrieve(
                query, 
                top_k=top_k,
                vendor=vendor,
                doc_type=doc_type,
            )
            
            # Check if results are documentation
            is_documentation = any(
                doc.get("metadata", {}).get("vendor") 
                for doc in retrieved_docs
            )

            # Format context
            context = self.format_context(retrieved_docs, include_source=True)

            # Inject context into prompt
            enhanced_prompt = self.inject_context(
                system_prompt=system_prompt,
                context=context,
                query=query,
                is_documentation=is_documentation,
            )

            # Build context sources with citations
            context_sources = []
            for i, doc in enumerate(retrieved_docs):
                metadata = doc.get("metadata", {})
                context_sources.append({
                    "id": doc.get("id"),
                    "title": metadata.get("title", "Unknown"),
                    "source": metadata.get("source", ""),
                    "score": doc.get("score", 0),
                    "citation_id": f"[{i+1}]",  # Citation marker
                    "chunk_index": metadata.get("chunk_index"),
                    "total_chunks": metadata.get("total_chunks"),
                    "vendor": metadata.get("vendor"),
                    "doc_type": metadata.get("doc_type"),
                })
            
            return {
                "enhanced_prompt": enhanced_prompt,
                "context": context,
                "retrieved_docs": retrieved_docs,
                "context_sources": context_sources,
                "citations": self._format_citations(context_sources),
                "is_documentation": is_documentation,
            }

        except Exception as e:
            logger.error("rag_query_error", error=str(e), query=query[:50])
            # Return original prompt if RAG fails
            return {
                "enhanced_prompt": system_prompt,
                "context": "",
                "retrieved_docs": [],
                "context_sources": [],
                "citations": [],
                "is_documentation": False,
            }

    def set_top_k(self, top_k: int) -> None:
        """
        Set number of documents to retrieve
        
        Args:
            top_k: Number of documents
        """
        self.top_k = top_k

    def set_similarity_threshold(self, threshold: float) -> None:
        """
        Set similarity threshold
        
        Args:
            threshold: Similarity threshold (0.0 to 1.0)
        """
        self.similarity_threshold = threshold

    def _format_citations(self, context_sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Format citations for source attribution
        
        Args:
            context_sources: List of context sources
            
        Returns:
            Formatted citations
        """
        citations = []
        for source in context_sources:
            citation = {
                "id": source.get("citation_id"),
                "title": source.get("title"),
                "source": source.get("source"),
                "confidence": min(source.get("score", 0.0), 1.0),
            }
            
            # Add URL if available
            if source.get("source", "").startswith("http"):
                citation["url"] = source.get("source")
            
            citations.append(citation)
        
        return citations

    def format_context_with_citations(
        self,
        retrieved_docs: List[Dict[str, Any]],
        max_length: int = 2000,
    ) -> tuple[str, List[Dict[str, Any]]]:
        """
        Format context with citation markers
        
        Args:
            retrieved_docs: Retrieved documents
            max_length: Maximum context length
            
        Returns:
            Tuple of (formatted_context, citations)
        """
        if not retrieved_docs:
            return "", []
        
        context_parts = []
        citations = []
        total_length = 0
        
        for i, doc in enumerate(retrieved_docs):
            metadata = doc.get("metadata", {})
            content = metadata.get("content", "")
            if not content:
                content = metadata.get("text", "")
            
            title = metadata.get("title", "Unknown")
            citation_id = f"[{i+1}]"
            
            # Format with citation marker
            formatted = f"{citation_id} [{title}]\n{content}\n\n"
            
            if total_length + len(formatted) > max_length:
                break
            
            context_parts.append(formatted)
            total_length += len(formatted)
            
            # Add citation
            citations.append({
                "id": citation_id,
                "title": title,
                "source": metadata.get("source", ""),
                "score": doc.get("score", 0.0),
            })
        
        context = "\n".join(context_parts).strip()
        return context, citations

