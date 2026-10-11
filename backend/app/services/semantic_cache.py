"""语义缓存：对语义相似的问题命中缓存答案，降低 LLM 调用量与成本。"""
import math
import threading

from cachetools import TTLCache

from app.config import settings


def _cosine(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


class SemanticCache:
    def __init__(self, threshold: float = 0.95, ttl: int = 1800, maxsize: int = 512):
        self._store = TTLCache(maxsize=maxsize, ttl=ttl)
        self._threshold = threshold
        self._lock = threading.Lock()

    def get(self, query_embedding: list[float]):
        with self._lock:
            for key_emb, value in self._store.items():
                if _cosine(key_emb, query_embedding) >= self._threshold:
                    return value
        return None

    def put(self, query_embedding: list[float], value) -> None:
        with self._lock:
            self._store[tuple(query_embedding)] = value


_cache = SemanticCache()


def lookup(query_embedding):
    if not settings.SEMANTIC_CACHE_ENABLED:
        return None
    return _cache.get(query_embedding)


def store(query_embedding, value) -> None:
    if not settings.SEMANTIC_CACHE_ENABLED:
        return
    _cache.put(query_embedding, value)
