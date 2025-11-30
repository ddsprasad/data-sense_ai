"""
Response caching for LLM and SQL query results.
Provides in-memory caching with TTL for faster repeated queries.
"""
import hashlib
import time
from typing import Optional, Dict, Any
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class ResponseCache:
    """In-memory cache for question responses with TTL."""

    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache.

        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def _generate_key(self, question: str, question_type: str = "original") -> str:
        """Generate a cache key from the question."""
        normalized = question.lower().strip()
        key_string = f"{question_type}:{normalized}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def get(self, question: str, question_type: str = "original") -> Optional[Dict[str, Any]]:
        """
        Get cached response for a question.

        Args:
            question: The user's question
            question_type: Type of question (original, followup, etc.)

        Returns:
            Cached response dict or None if not found/expired
        """
        key = self._generate_key(question, question_type)

        if key in self._cache:
            entry = self._cache[key]
            if time.time() < entry['expires_at']:
                self.hits += 1
                logger.info(f"Cache HIT for question: {question[:50]}...")
                return entry['data']
            else:
                # Expired, remove it
                del self._cache[key]

        self.misses += 1
        logger.info(f"Cache MISS for question: {question[:50]}...")
        return None

    def set(self, question: str, response: Dict[str, Any],
            question_type: str = "original", ttl: Optional[int] = None) -> None:
        """
        Cache a response for a question.

        Args:
            question: The user's question
            response: The response data to cache
            question_type: Type of question
            ttl: Time-to-live in seconds (uses default if not specified)
        """
        key = self._generate_key(question, question_type)
        expires_at = time.time() + (ttl or self.default_ttl)

        self._cache[key] = {
            'data': response,
            'expires_at': expires_at,
            'created_at': time.time()
        }
        logger.info(f"Cached response for question: {question[:50]}...")

    def invalidate(self, question: str, question_type: str = "original") -> bool:
        """Remove a specific entry from cache."""
        key = self._generate_key(question, question_type)
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self.hits = 0
        self.misses = 0

    def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count of removed entries."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time >= entry['expires_at']
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        return {
            'size': len(self._cache),
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%"
        }


# Global cache instance
_response_cache = ResponseCache(default_ttl=3600)  # 1 hour default


def get_response_cache() -> ResponseCache:
    """Get the global response cache instance."""
    return _response_cache


def cached_response(question_type: str = "original", ttl: int = 3600):
    """
    Decorator for caching function responses based on question.

    Args:
        question_type: Type identifier for the cache key
        ttl: Cache TTL in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to extract question from args or kwargs
            question = kwargs.get('query') or kwargs.get('question')
            if question is None and len(args) > 2:
                question = args[2]  # Usually the 3rd argument

            if question:
                cache = get_response_cache()
                cached = cache.get(question, question_type)
                if cached is not None:
                    return cached

                # Execute function and cache result
                result = func(*args, **kwargs)

                # Only cache successful responses
                if result and not isinstance(result, Exception):
                    cache.set(question, result, question_type, ttl)

                return result

            return func(*args, **kwargs)
        return wrapper
    return decorator
