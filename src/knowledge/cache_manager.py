"""Cache manager for knowledge base queries"""

import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

import redis
from openai import OpenAI

from src.utils.config import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class QueryCache:
    """Cache for query results"""

    def __init__(self, redis_url: Optional[str] = None, ttl: int = 3600):
        """
        Initialize query cache
        
        Args:
            redis_url: Redis URL
            ttl: Time to live in seconds (default 1 hour)
        """
        try:
            self.redis_client = redis.from_url(redis_url or settings.REDIS_URL)
            self.ttl = ttl
        except Exception as e:
            logger.warning("redis_cache_init_failed", error=str(e))
            self.redis_client = None

    def _get_cache_key(self, query: str, namespace: Optional[str] = None) -> str:
        """Generate cache key"""
        content = f"{namespace}:{query}" if namespace else query
        hash_obj = hashlib.sha256(content.encode())
        return f"kb_query:{hash_obj.hexdigest()}"

    def get(self, query: str, namespace: Optional[str] = None) -> Optional[List[Dict[str, Any]]]:
        """Get cached query results"""
        if not self.redis_client:
            return None
        
        try:
            key = self._get_cache_key(query, namespace)
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning("cache_get_error", error=str(e))
        
        return None

    def set(
        self,
        query: str,
        results: List[Dict[str, Any]],
        namespace: Optional[str] = None,
    ) -> None:
        """Cache query results"""
        if not self.redis_client:
            return
        
        try:
            key = self._get_cache_key(query, namespace)
            self.redis_client.setex(key, self.ttl, json.dumps(results))
        except Exception as e:
            logger.warning("cache_set_error", error=str(e))

    def invalidate(self, pattern: str) -> None:
        """Invalidate cache entries matching pattern"""
        if not self.redis_client:
            return
        
        try:
            keys = self.redis_client.keys(f"kb_query:*{pattern}*")
            if keys:
                self.redis_client.delete(*keys)
        except Exception as e:
            logger.warning("cache_invalidate_error", error=str(e))


class EmbeddingCache:
    """Cache for embeddings"""

    def __init__(self, redis_url: Optional[str] = None, ttl: int = 86400 * 7):
        """
        Initialize embedding cache
        
        Args:
            redis_url: Redis URL
            ttl: Time to live in seconds (default 7 days)
        """
        try:
            self.redis_client = redis.from_url(redis_url or settings.REDIS_URL)
            self.ttl = ttl
        except Exception as e:
            logger.warning("redis_embedding_cache_init_failed", error=str(e))
            self.redis_client = None

    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key for embedding"""
        content = f"{model}:{text}"
        hash_obj = hashlib.md5(content.encode())
        return f"kb_embedding:{hash_obj.hexdigest()}"

    def get(self, text: str, model: str) -> Optional[List[float]]:
        """Get cached embedding"""
        if not self.redis_client:
            return None
        
        try:
            key = self._get_cache_key(text, model)
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
        except Exception as e:
            logger.warning("embedding_cache_get_error", error=str(e))
        
        return None

    def set(self, text: str, model: str, embedding: List[float]) -> None:
        """Cache embedding"""
        if not self.redis_client:
            return
        
        try:
            key = self._get_cache_key(text, model)
            self.redis_client.setex(key, self.ttl, json.dumps(embedding))
        except Exception as e:
            logger.warning("embedding_cache_set_error", error=str(e))


class PrecomputedQueryCache:
    """Cache for precomputed common queries"""

    def __init__(self, redis_url: Optional[str] = None):
        """Initialize precomputed query cache"""
        try:
            self.redis_client = redis.from_url(redis_url or settings.REDIS_URL)
        except Exception as e:
            logger.warning("redis_precomputed_cache_init_failed", error=str(e))
            self.redis_client = None

    def precompute_common_queries(
        self,
        queries: List[str],
        search_func,
        namespace: Optional[str] = None,
    ) -> None:
        """
        Precompute results for common queries
        
        Args:
            queries: List of common queries
            search_func: Function to perform search
            namespace: Optional namespace
        """
        if not self.redis_client:
            return
        
        for query in queries:
            try:
                results = await search_func(query, namespace=namespace)
                cache = QueryCache()
                cache.set(query, results, namespace)
            except Exception as e:
                logger.warning("precompute_query_error", query=query[:50], error=str(e))


class CacheManager:
    """Unified cache manager for knowledge base"""

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize cache manager
        
        Args:
            redis_url: Redis URL
        """
        self.query_cache = QueryCache(redis_url)
        self.embedding_cache = EmbeddingCache(redis_url)
        self.precomputed_cache = PrecomputedQueryCache(redis_url)

    def get_query_results(
        self,
        query: str,
        namespace: Optional[str] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """Get cached query results"""
        return self.query_cache.get(query, namespace)

    def cache_query_results(
        self,
        query: str,
        results: List[Dict[str, Any]],
        namespace: Optional[str] = None,
    ) -> None:
        """Cache query results"""
        self.query_cache.set(query, results, namespace)

    def get_embedding(
        self,
        text: str,
        model: str,
    ) -> Optional[List[float]]:
        """Get cached embedding"""
        return self.embedding_cache.get(text, model)

    def cache_embedding(
        self,
        text: str,
        model: str,
        embedding: List[float],
    ) -> None:
        """Cache embedding"""
        self.embedding_cache.set(text, model, embedding)

    def invalidate_namespace(self, namespace: str) -> None:
        """Invalidate all cache entries for a namespace"""
        self.query_cache.invalidate(namespace)

