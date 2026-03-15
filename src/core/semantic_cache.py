"""
Semantic Caching Layer.

This module provides an enterprise-grade semantic caching mechanism using Redis
and cosine similarity to cache LLM responses, optimizing latency and Azure OpenAI costs.
"""

import json
import logging
from typing import Optional, Dict, Any, Tuple
import numpy as np

# In a real environment, you'd use a robust Redis client like 'redis' or 'redis.asyncio'
# and an embedding model from LangChain or Azure OpenAI directly.
# For this implementation, we simulate the Redis connection and embedding process.
try:
    import redis
except ImportError:
    redis = None

logger = logging.getLogger(__name__)

class SemanticCache:
    """
    Implements a semantic caching layer for LLM responses.
    
    Uses Redis as the backing store and cosine similarity for matching
    semantic queries to save on redundant LLM calls.
    """

    def __init__(
        self, 
        redis_host: str = "localhost", 
        redis_port: int = 6379, 
        redis_password: str = "",
        similarity_threshold: float = 0.95
    ) -> None:
        """
        Initializes the SemanticCache.

        Args:
            redis_host (str): Redis server hostname.
            redis_port (int): Redis server port.
            redis_password (str): Redis server password.
            similarity_threshold (float): The cosine similarity threshold (0.0 to 1.0) 
                                          above which a cache hit is considered valid.
        """
        self.similarity_threshold = similarity_threshold
        self._redis_client: Optional[Any] = None
        
        try:
            if redis:
                self._redis_client = redis.Redis(
                    host=redis_host, 
                    port=redis_port, 
                    password=redis_password,
                    decode_responses=False # Keep raw for vector operations if needed, but we'll manage serialization
                )
                # Test connection
                self._redis_client.ping()
                logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
            else:
                logger.warning("Redis library not installed. Semantic cache will operate in dummy mode.")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
            # Decide if we want to fail hard or fallback to no-op
            self._redis_client = None

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculates the cosine similarity between two vectors.

        Args:
            vec1 (np.ndarray): The first vector.
            vec2 (np.ndarray): The second vector.

        Returns:
            float: The cosine similarity score.
        """
        if vec1.shape != vec2.shape:
            raise ValueError("Vectors must have the same dimensions.")
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return float(dot_product / (norm1 * norm2))

    def _get_embedding(self, text: str) -> np.ndarray:
        """
        Generates an embedding for the given text.
        (Mock implementation - replace with actual Azure OpenAI embedding call).

        Args:
            text (str): The text to embed.

        Returns:
            np.ndarray: The vector embedding.
        """
        # MOCK: In production, call AzureOpenAIEmbeddings here.
        # Returning a dummy normalized vector based on string length and hash for simulation
        np.random.seed(hash(text) % (2**32))
        vec = np.random.rand(1536) # Standard dimensionality for text-embedding-ada-002 / text-embedding-3-small
        return vec / np.linalg.norm(vec)

    def get_cached_response(self, query: str) -> Optional[str]:
        """
        Retrieves a semantically similar cached response if it exceeds the threshold.

        Args:
            query (str): The user query.

        Returns:
            Optional[str]: The cached response if a match is found, otherwise None.
        """
        if not self._redis_client:
            return None

        try:
            query_embedding = self._get_embedding(query)
            
            # Note: In a true production Azure environment, we would use Azure Cache for Redis
            # Enterprise with RediSearch module for built-in vector similarity search (VSS).
            # This is a basic demonstration of the logic across all keys.
            
            best_match_score = -1.0
            best_response = None
            
            # WARNING: SCAN is inefficient for large datasets. Use Redis VSS in production.
            for key in self._redis_client.scan_iter(match="cache:*"):
                cached_data_bytes = self._redis_client.get(key)
                if not cached_data_bytes:
                    continue
                    
                cached_data = json.loads(cached_data_bytes.decode('utf-8'))
                cached_embedding = np.array(cached_data['embedding'])
                
                score = self.cosine_similarity(query_embedding, cached_embedding)
                
                if score > best_match_score and score >= self.similarity_threshold:
                    best_match_score = score
                    best_response = cached_data['response']

            if best_response:
                logger.info(f"Semantic cache HIT. Score: {best_match_score:.4f}")
                return best_response
            
            logger.info("Semantic cache MISS.")
            return None

        except Exception as e:
            logger.error(f"Error during cache retrieval: {e}", exc_info=True)
            return None

    def set_cache_response(self, query: str, response: str, ttl_seconds: int = 86400) -> None:
        """
        Caches the response along with the query's embedding.

        Args:
            query (str): The original user query.
            response (str): The LLM response to cache.
            ttl_seconds (int): Time-to-live for the cache entry in seconds. Default is 24 hours.
        """
        if not self._redis_client:
            return

        try:
            query_embedding = self._get_embedding(query)
            
            # Create a unique key based on hash (or use a UUID)
            cache_key = f"cache:{hash(query)}"
            
            cache_payload = {
                "query": query,
                "embedding": query_embedding.tolist(),
                "response": response
            }
            
            self._redis_client.setex(
                name=cache_key,
                time=ttl_seconds,
                value=json.dumps(cache_payload)
            )
            logger.info(f"Successfully cached response for query. Key: {cache_key}")
            
        except Exception as e:
            logger.error(f"Error setting cache response: {e}", exc_info=True)
