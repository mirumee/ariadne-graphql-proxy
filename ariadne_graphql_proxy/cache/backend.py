from time import time
from typing import Any, Dict, Optional, Tuple


class CacheBackend:
    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        raise NotImplementedError("Cache backends need to define custom 'set' method.")

    async def get(self, key: str, default: Any = None) -> Any:
        raise NotImplementedError("Cache backends need to define custom 'get' method.")

    async def clear_all(self):
        raise NotImplementedError(
            "Cache backends need to define custom 'clear_all' method."
        )


class InMemoryCache(CacheBackend):
    _cache: Dict[str, Tuple[Any, Optional[int]]]

    def __init__(self):
        self._cache = {}

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        self._cache[key] = value, int(time() + ttl) if ttl else None

    async def get(self, key: str, default: Any = None) -> Any:
        if key not in self._cache:
            return default

        cache, ttl = self._cache[key]
        if ttl and ttl < time():
            del self._cache[key]
            return default

        return cache

    async def clear_all(self):
        self._cache = {}
