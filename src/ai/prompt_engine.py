"""Prompt engineering system"""

from typing import Dict, Any, Optional, List

from src.templates.template_loader import TemplateLoader
from src.knowledge.rag_pipeline import RAGPipeline
from src.knowledge.hybrid_search import HybridSearch
from src.knowledge.reranker import Reranker
from src.knowledge.cache_manager import CacheManager
from src.knowledge.voice_formatter import VoiceFormatter
from src.knowledge.proactive_retrieval import ProactiveRetrieval
from src.knowledge.query_processor import QueryProcessor
from src.ai.conversation_manager import ConversationManager
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PromptEngine:
    """Dynamic prompt construction and management"""

    def __init__(
        self,
        template_loader: TemplateLoader,
        rag_pipeline: Optional[RAGPipeline] = None,
        business_id: Optional[str] = None,
    ):
        """
        Initialize prompt engine
        
        Args:
            template_loader: Template loader instance
            rag_pipeline: Optional RAG pipeline for knowledge injection
            business_id: Optional business ID for namespace isolation
        """
        self.template_loader = template_loader
        self.rag_pipeline = rag_pipeline or RAGPipeline(business_id=business_id)
        self.hybrid_search = HybridSearch()
        self.reranker = Reranker()
        self.cache_manager = CacheManager()
        self.voice_formatter = VoiceFormatter()
        self.proactive_retrieval = ProactiveRetrieval()
        self.query_processor = QueryProcessor()
        self.active_templates: Dict[str, Dict[str, Any]] = {}

    def load_template(self, template_name: str) -> Dict[str, Any]:
        """
        Load a business template
        
        Args:
            template_name: Template name
            
        Returns:
            Template configuration
        """
        template = self.template_loader.load_template(template_name)
        self.active_templates[template_name] = template
        return template

    def build_system_prompt(
        self,
        template_name: str,
        conversation_manager: Optional[ConversationManager] = None,
        additional_context: Optional[str] = None,
    ) -> str:
        """
        Build system prompt from template and context
        
        Args:
            template_name: Template name
            conversation_manager: Optional conversation manager for context
            additional_context: Optional additional context string
            
        Returns:
            Complete system prompt
        """
        # Load template if not already loaded
        if template_name not in self.active_templates:
            self.load_template(template_name)

        template = self.active_templates[template_name]
        ai_config = self.template_loader.get_ai_config(template)

        # Start with base system prompt
        system_prompt = ai_config.get("system_prompt", "You are a helpful assistant.")

        # Add conversation context if available
        if conversation_manager:
            context_summary = conversation_manager.get_context_summary()
            if context_summary:
                system_prompt += f"\n\n## Conversation Context\n{context_summary}"

        # Add additional context
        if additional_context:
            system_prompt += f"\n\n## Additional Context\n{additional_context}"

        return system_prompt

    async def build_enhanced_prompt(
        self,
        template_name: str,
        user_query: str,
        conversation_manager: Optional[ConversationManager] = None,
        use_rag: bool = True,
        optimize_for_voice: bool = False,
        timeout: float = 2.0,
    ) -> Dict[str, Any]:
        """
        Build enhanced prompt with RAG context
        
        Args:
            template_name: Template name
            user_query: Current user query
            conversation_manager: Optional conversation manager
            use_rag: Whether to use RAG for knowledge retrieval
            optimize_for_voice: Whether to optimize for voice output
            timeout: Timeout for RAG operations (seconds)
            
        Returns:
            Dictionary with enhanced prompt and metadata
        """
        # Build base system prompt
        base_prompt = self.build_system_prompt(
            template_name=template_name,
            conversation_manager=conversation_manager,
        )

        # Use RAG if enabled and available
        if use_rag and self.rag_pipeline:
            try:
                # Check cache first for voice optimization
                if optimize_for_voice:
                    cached_results = self.cache_manager.get_query_results(
                        query=user_query,
                        namespace=self.rag_pipeline.business_id,
                    )
                    if cached_results:
                        # Use cached results
                        context = self.voice_formatter.format_for_voice(
                            cached_results,
                            query=user_query,
                            prioritize_brevity=True,
                        )
                        return {
                            "system_prompt": self._inject_context(base_prompt, context, user_query),
                            "context": context,
                            "sources": [r.get("metadata", {}) for r in cached_results[:3]],
                            "has_rag_context": bool(context),
                            "from_cache": True,
                        }
                
                # Process query
                processed_query = self.query_processor.process(
                    query=user_query,
                    conversation_history=conversation_manager.get_conversation_history(limit=5) if conversation_manager else None,
                )
                
                # Perform hybrid search
                search_results = await self.hybrid_search.search(
                    query=processed_query["processed_query"],
                    top_k=10 if not optimize_for_voice else 5,
                    namespace=self.rag_pipeline.business_id,
                )
                
                # Rerank results
                reranked_results = await self.reranker.rerank(
                    query=processed_query["processed_query"],
                    results=search_results,
                    top_k=5 if not optimize_for_voice else 3,
                )
                
                # Format context
                if optimize_for_voice:
                    context = self.voice_formatter.format_for_voice(
                        reranked_results,
                        query=user_query,
                        prioritize_brevity=True,
                    )
                else:
                    context = self.rag_pipeline.format_context(reranked_results)
                
                # Cache results
                self.cache_manager.cache_query_results(
                    query=user_query,
                    results=reranked_results,
                    namespace=self.rag_pipeline.business_id,
                )
                
                # Build sources
                sources = [
                    {
                        "title": r.get("metadata", {}).get("title", "Unknown"),
                        "source": r.get("metadata", {}).get("source", ""),
                        "score": r.get("score", 0.0),
                    }
                    for r in reranked_results[:3]
                ]
                
                return {
                    "system_prompt": self._inject_context(base_prompt, context, user_query),
                    "context": context,
                    "sources": sources,
                    "has_rag_context": bool(context),
                    "from_cache": False,
                }
                
            except Exception as e:
                logger.error("rag_prompt_enhancement_error", error=str(e))
                # Fall back to base prompt
                return {
                    "system_prompt": base_prompt,
                    "context": "",
                    "sources": [],
                    "has_rag_context": False,
                }

        return {
            "system_prompt": base_prompt,
            "context": "",
            "sources": [],
            "has_rag_context": False,
        }
    
    def _inject_context(self, system_prompt: str, context: str, query: Optional[str] = None) -> str:
        """Inject context into system prompt"""
        if not context:
            return system_prompt
        
        context_section = f"""
## Knowledge Base Context

The following information is available from the knowledge base:

{context}

Use this information to provide accurate and helpful responses. If the information doesn't answer the question, say so and offer to help in other ways.
"""
        
        enhanced_prompt = f"{system_prompt}\n\n{context_section}"
        
        if query:
            enhanced_prompt += f"\n\nCurrent question: {query}"
        
        return enhanced_prompt

    def get_ai_parameters(self, template_name: str) -> Dict[str, Any]:
        """
        Get AI model parameters from template
        
        Args:
            template_name: Template name
            
        Returns:
            Dictionary of AI parameters
        """
        if template_name not in self.active_templates:
            self.load_template(template_name)

        template = self.active_templates[template_name]
        ai_config = self.template_loader.get_ai_config(template)

        return {
            "model": ai_config.get("model", "gpt-4o"),
            "temperature": ai_config.get("temperature", 0.7),
            "max_tokens": ai_config.get("max_tokens", 1000),
        }

    def get_voice_parameters(self, template_name: str) -> Dict[str, Any]:
        """
        Get voice parameters from template
        
        Args:
            template_name: Template name
            
        Returns:
            Dictionary of voice parameters
        """
        if template_name not in self.active_templates:
            self.load_template(template_name)

        template = self.active_templates[template_name]
        voice_config = self.template_loader.get_voice_config(template)

        return {
            "voice": voice_config.get("voice", "alloy"),
            "language": voice_config.get("language", "en-US"),
            "response_delay": voice_config.get("response_delay", 0.5),
        }

    def inject_custom_instructions(
        self,
        system_prompt: str,
        instructions: List[str],
    ) -> str:
        """
        Inject custom instructions into system prompt
        
        Args:
            system_prompt: Base system prompt
            instructions: List of custom instructions
            
        Returns:
            Enhanced system prompt
        """
        if not instructions:
            return system_prompt

        instructions_text = "\n".join(f"- {instruction}" for instruction in instructions)
        return f"{system_prompt}\n\n## Additional Instructions\n{instructions_text}"

    def inject_customer_info(
        self,
        system_prompt: str,
        customer_info: Dict[str, Any],
    ) -> str:
        """
        Inject customer information into system prompt
        
        Args:
            system_prompt: Base system prompt
            customer_info: Customer information dictionary
            
        Returns:
            Enhanced system prompt
        """
        if not customer_info:
            return system_prompt

        info_parts = []
        if "name" in customer_info:
            info_parts.append(f"Customer Name: {customer_info['name']}")
        if "account_type" in customer_info:
            info_parts.append(f"Account Type: {customer_info['account_type']}")
        if "previous_interactions" in customer_info:
            info_parts.append(f"Previous Interactions: {customer_info['previous_interactions']}")

        if info_parts:
            info_text = "\n".join(info_parts)
            return f"{system_prompt}\n\n## Customer Information\n{info_text}"

        return system_prompt

