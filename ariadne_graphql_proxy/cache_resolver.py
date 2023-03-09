import hashlib
import json
from functools import wraps
from inspect import isawaitable
from typing import Any, Optional

from graphql import GraphQLResolveInfo

from .print_operation import print_operation_field


class CacheBackend:
    def __init__(self):
        self._cache = {}

    async def set(self, key: str, value: Any):
        self._cache[key] = value

    async def get(self, key: str, default: Any) -> Any:
        return self._cache.get(key, default)


def cache_resolver(backend: CacheBackend, prefix: Optional[str] = None):
    def cache_decorator(resolver):
        @wraps(resolver)
        async def caching_resolver(obj, info, **kwargs):
            cache_key = get_cache_key(obj, info, kwargs, prefix)
            data = await backend.get(cache_key, "miss")
            if data != "miss":
                return data

            fresh_data = resolver(obj, info, **kwargs)
            if isawaitable(fresh_data):
                fresh_data = await fresh_data

            data = await backend.set(cache_key, fresh_data)
            return fresh_data

        return caching_resolver

    return cache_decorator


def get_cache_key(
    obj: Any,
    info: GraphQLResolveInfo,
    kwargs: Any,
    prefix: Optional[str] = None,
) -> str:
    hash = hashlib.md5(
        json.dumps(
            {
                "prefix": prefix,
                "obj": obj,
                "args": kwargs,
                "fields": sorted(
                    [print_operation_field(field) for field in info.field_nodes]
                ),
            }
        ).encode("utf-8")
    ).hexdigest()

    if prefix:
        return f"{prefix}_{hash}"

    return hash
