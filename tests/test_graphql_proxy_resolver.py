import pytest

from ariadne_graphql_proxy import GraphQLProxyResolver, set_resolver
from ariadne_graphql_proxy.cache import InMemoryCache


@pytest.fixture
def cache_backend():
    return InMemoryCache()


@pytest.fixture
def schema_with_cached_resolver(schema, cache_backend):
    resolver = GraphQLProxyResolver(
        url="http://upstream.example.com/graphql/",
        proxy_headers=True,
        cache=cache_backend,
        cache_key="test_key",
    )

    set_resolver(schema, "Query", "basic", resolver)
    set_resolver(schema, "Query", "complex", resolver)
    return schema
