from functools import wraps
from inspect import isawaitable
from typing import Any, Callable, Optional, Union

from graphql import GraphQLResolveInfo

from .backend import CacheBackend
from .cache_key import get_info_cache_key


class NoCache:
    pass


def cached_resolver(
    backend: CacheBackend,
    prefix: Optional[Union[str, Callable[[GraphQLResolveInfo], str]]] = None,
    ttl: Optional[int] = None,
):
    def make_resolver_cached(f):
        @wraps(f)
        async def caching_resolver(obj: Any, info: GraphQLResolveInfo, **kwargs):
            query_cache_key = get_info_cache_key(obj, info, kwargs, prefix)
            cached_result = await backend.get(query_cache_key, NoCache)
            if cached_result is not NoCache:
                return cached_result

            result = f(obj, info, **kwargs)
            if isawaitable(result):
                result = await result

            await backend.set(query_cache_key, result, ttl)
            return result

        return caching_resolver

    return make_resolver_cached
