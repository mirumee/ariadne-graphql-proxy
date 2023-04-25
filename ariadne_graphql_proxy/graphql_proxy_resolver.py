from typing import Any, Callable, List, Optional, Union

from graphql import GraphQLResolveInfo, OperationDefinitionNode
from httpx import AsyncClient

from .narrow_graphql_query import narrow_graphql_query
from .print import print_operation
from .cache import CacheBackend, get_operation_cache_key


class NoCache:
    pass


class GraphQLProxyResolver:
    _url: str
    _proxy_headers: Optional[Union[bool, Callable, List[str]]]

    _cache: Optional[CacheBackend]
    _cache_key: Optional[Union[str, Callable[[GraphQLResolveInfo], str]]]
    _cache_ttl: Optional[int]

    def __init__(
        self,
        url: str,
        proxy_headers: Optional[Union[bool, List[str]]] = None,
        cache: Optional[CacheBackend] = None,
        cache_key: Optional[Union[str, Callable[[GraphQLResolveInfo], str]]] = None,
        cache_ttl: Optional[int] = None,
    ):
        self._url = url
        self._proxy_headers = proxy_headers

        self._cache = cache
        self._cache_key = cache_key
        self._cache_ttl = cache_ttl

    async def __call__(self, obj: Any, info: GraphQLResolveInfo, **arguments) -> Any:
        operation_node, variables_used = narrow_graphql_query(info)
        payload = {
            "operationName": operation_node.name.value,
            "query": print_operation(operation_node),
            "variables": {
                argument: arguments[argument]
                for argument in arguments
                if argument in variables_used
            },
        }

        if self._cache and self._cache_key:
            return await self.proxy_query_with_cache(obj, info, payload, operation_node)

        return await self.proxy_query(obj, info, payload)

    async def proxy_query_with_cache(
        self,
        obj: Any,
        info: GraphQLResolveInfo,
        payload: dict,
        operation_node: OperationDefinitionNode,
    ) -> dict:
        if callable(self._cache_key):
            cache_key_final = self._cache_key(info)
        else:
            cache_key_final = self._cache_key

        query_cache_key = get_operation_cache_key(
            obj,
            operation_node,
            payload["variables"],
            cache_key_final,
        )

        cached_result = await self._cache.get(query_cache_key, NoCache)
        if cached_result is not NoCache:
            return cached_result

        result = self.proxy_query(obj, info, payload)

        await self._cache.set(query_cache_key, result, self._cache_ttl)
        return result

    async def proxy_query(
        self, obj: Any, info: GraphQLResolveInfo, payload: dict
    ) -> dict:
        if self._proxy_headers is True:
            proxy_headers = info.context["headers"]
        elif callable(self._proxy_headers):
            proxy_headers = self._proxy_headers(obj, info, payload)
        elif self._proxy_headers:
            proxy_headers = {
                header: value
                for header, value in info.context["headers"]
                if header in self._proxy_headers
            }
        else:
            proxy_headers = None

        async with AsyncClient() as client:
            r = await client.post(
                self.url,
                json=payload,
                headers=proxy_headers,
            )

            response_json = r.json()
            return response_json["data"]
