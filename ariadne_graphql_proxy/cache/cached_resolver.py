from functools import wraps
from inspect import isawaitable
from typing import Any, Callable, Optional, Union

from graphql import GraphQLResolveInfo

from .backend import CacheBackend
from .cache_key import get_cache_key


class NoCache:
    pass


def cached_resolver(
    cache: CacheBackend,
    cache_key: Union[str, Callable[[GraphQLResolveInfo], str]],
    ttl: Optional[int] = None,
):
    def make_resolver_cached(f):
        @wraps(f)
        async def caching_resolver(obj: Any, info: GraphQLResolveInfo, **kwargs):
            if callable(cache_key):
                cache_key = cache_key(info)

            query_cache_key = get_cache_key(obj, info, kwargs, cache_key)
            cached_result = await cache.get(query_cache_key, NoCache)
            if cached_result is not NoCache:
                return cached_result

            result = f(obj, info, **kwargs)
            if isawaitable(result):
                result = await result

            await cache.set(query_cache_key, result, ttl)
            return result

        return caching_resolver

    return make_resolver_cached
