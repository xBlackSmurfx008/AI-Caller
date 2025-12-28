"""Multi-model embedding support with caching"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from enum import Enum
import hashlib
import json

from openai import OpenAI
import redis

from src.utils.config import get_settings
from src.utils.errors import KnowledgeBaseError
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class EmbeddingModel(str, Enum):
    """Embedding model enumeration"""
    OPENAI_TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"
    OPENAI_TEXT_EMBEDDING_3_LARGE = "text-embedding-3-large"
    OPENAI_TEXT_EMBEDDING_ADA_002 = "text-embedding-ada-002"
    COHERE_EMBED_ENGLISH_V3 = "embed-english-v3.0"
    COHERE_EMBED_MULTILINGUAL_V3 = "embed-multilingual-v3.0"
    LOCAL_SENTENCE_TRANSFORMERS = "local-sentence-transformers"


class BaseEmbeddingProvider(ABC):
    """Base class for embedding providers"""

    @abstractmethod
    async def embed(self, texts: List[str], **kwargs) -> List[List[float]]:
        """
        Generate embeddings for texts
        
        Args:
            texts: List of texts to embed
            **kwargs: Additional parameters
            
        Returns:
            List of embedding vectors
        """
        pass

    @abstractmethod
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get model name"""
        pass


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI embedding provider"""

    def __init__(self, model: str = "text-embedding-3-small", api_key: Optional[str] = None):
        """
        Initialize OpenAI embedding provider
        
        Args:
            model: Model name
            api_key: OpenAI API key (defaults to settings)
        """
        self.model = model
        self.client = OpenAI(api_key=api_key or settings.OPENAI_API_KEY)
        
        # Dimension mapping
        self.dimensions = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536,
        }

    async def embed(self, texts: List[str], **kwargs) -> List[List[float]]:
        """Generate embeddings using OpenAI"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error("openai_embedding_error", error=str(e), model=self.model)
            raise KnowledgeBaseError(f"Failed to generate OpenAI embeddings: {str(e)}") from e

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.dimensions.get(self.model, 1536)

    def get_model_name(self) -> str:
        """Get model name"""
        return self.model


class SentenceTransformersProvider(BaseEmbeddingProvider):
    """Local sentence transformers provider"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize sentence transformers provider
        
        Args:
            model_name: Model name
        """
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            self.model_name = model_name
        except ImportError:
            raise KnowledgeBaseError("sentence-transformers is required for local embeddings")
        except Exception as e:
            logger.error("sentence_transformer_init_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to initialize sentence transformer: {str(e)}") from e

    async def embed(self, texts: List[str], **kwargs) -> List[List[float]]:
        """Generate embeddings using sentence transformers"""
        try:
            embeddings = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error("sentence_transformer_embedding_error", error=str(e))
            raise KnowledgeBaseError(f"Failed to generate embeddings: {str(e)}") from e

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.model.get_sentence_embedding_dimension()

    def get_model_name(self) -> str:
        """Get model name"""
        return self.model_name


class EmbeddingCache:
    """Cache for embeddings using Redis"""

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize embedding cache
        
        Args:
            redis_url: Redis URL (defaults to settings)
        """
        try:
            self.redis_client = redis.from_url(redis_url or settings.REDIS_URL)
            self.ttl = 86400 * 7  # 7 days
        except Exception as e:
            logger.warning("redis_cache_init_failed", error=str(e))
            self.redis_client = None

    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key for text and model"""
        content = f"{model}:{text}"
        hash_obj = hashlib.md5(content.encode())
        return f"embedding:{hash_obj.hexdigest()}"

    def get(self, text: str, model: str) -> Optional[List[float]]:
        """
        Get cached embedding
        
        Args:
            text: Text to look up
            model: Model name
            
        Returns:
            Cached embedding or None
        """
        if not self.redis_client:
            return None
        
        try:
            key = self._get_cache_key(text, model)
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning("cache_get_error", error=str(e))
        
        return None

    def set(self, text: str, model: str, embedding: List[float]) -> None:
        """
        Cache embedding
        
        Args:
            text: Text
            model: Model name
            embedding: Embedding vector
        """
        if not self.redis_client:
            return
        
        try:
            key = self._get_cache_key(text, model)
            self.redis_client.setex(key, self.ttl, json.dumps(embedding))
        except Exception as e:
            logger.warning("cache_set_error", error=str(e))

    def get_batch(self, texts: List[str], model: str) -> Dict[str, List[float]]:
        """
        Get multiple cached embeddings
        
        Args:
            texts: List of texts
            model: Model name
            
        Returns:
            Dictionary mapping text to embedding
        """
        if not self.redis_client:
            return {}
        
        cached = {}
        try:
            keys = [self._get_cache_key(text, model) for text in texts]
            values = self.redis_client.mget(keys)
            
            for text, value in zip(texts, values):
                if value:
                    cached[text] = json.loads(value)
        except Exception as e:
            logger.warning("cache_batch_get_error", error=str(e))
        
        return cached


class EmbeddingManager:
    """Manager for embedding generation with caching and multi-model support"""

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        provider: Optional[str] = None,
        use_cache: bool = True,
    ):
        """
        Initialize embedding manager
        
        Args:
            model: Model name
            provider: Provider type (openai, local, cohere)
            use_cache: Whether to use caching
        """
        self.model = model
        self.use_cache = use_cache
        
        # Initialize provider
        if provider == "local" or model == "local-sentence-transformers":
            self.provider = SentenceTransformersProvider()
        elif provider == "cohere":
            # Cohere provider would go here
            raise NotImplementedError("Cohere provider not yet implemented")
        else:
            # Default to OpenAI
            self.provider = OpenAIEmbeddingProvider(model=model)
        
        # Initialize cache
        self.cache = EmbeddingCache() if use_cache else None

    async def embed(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings with caching and batching
        
        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Check cache first
        cached_embeddings = {}
        texts_to_embed = []
        text_indices = []
        
        if self.cache:
            cached = self.cache.get_batch(texts, self.provider.get_model_name())
            for i, text in enumerate(texts):
                if text in cached:
                    cached_embeddings[i] = cached[text]
                else:
                    texts_to_embed.append(text)
                    text_indices.append(i)
        else:
            texts_to_embed = texts
            text_indices = list(range(len(texts)))
        
        # Generate embeddings for uncached texts
        new_embeddings = []
        if texts_to_embed:
            # Process in batches
            for i in range(0, len(texts_to_embed), batch_size):
                batch = texts_to_embed[i:i + batch_size]
                batch_indices = text_indices[i:i + batch_size]
                
                try:
                    batch_embeddings = await self.provider.embed(batch)
                    
                    # Cache new embeddings
                    if self.cache:
                        for text, embedding in zip(batch, batch_embeddings):
                            self.cache.set(text, self.provider.get_model_name(), embedding)
                    
                    # Store with original indices
                    for idx, embedding in zip(batch_indices, batch_embeddings):
                        new_embeddings.append((idx, embedding))
                except Exception as e:
                    logger.error("batch_embedding_error", error=str(e), batch_size=len(batch))
                    # Fallback: generate embeddings one by one
                    for text, idx in zip(batch, batch_indices):
                        try:
                            embedding = (await self.provider.embed([text]))[0]
                            if self.cache:
                                self.cache.set(text, self.provider.get_model_name(), embedding)
                            new_embeddings.append((idx, embedding))
                        except Exception as e2:
                            logger.error("single_embedding_error", error=str(e2), text=text[:50])
                            # Use zero vector as fallback
                            dim = self.provider.get_dimension()
                            new_embeddings.append((idx, [0.0] * dim))
        
        # Combine cached and new embeddings
        all_embeddings = {}
        all_embeddings.update(cached_embeddings)
        all_embeddings.update(dict(new_embeddings))
        
        # Return in original order
        return [all_embeddings[i] for i in range(len(texts))]

    def get_dimension(self) -> int:
        """Get embedding dimension"""
        return self.provider.get_dimension()

    def normalize_embeddings(self, embeddings: List[List[float]]) -> List[List[float]]:
        """
        Normalize embeddings to unit vectors
        
        Args:
            embeddings: List of embedding vectors
            
        Returns:
            Normalized embeddings
        """
        import numpy as np
        
        normalized = []
        for emb in embeddings:
            emb_array = np.array(emb)
            norm = np.linalg.norm(emb_array)
            if norm > 0:
                normalized.append((emb_array / norm).tolist())
            else:
                normalized.append(emb)
        
        return normalized

