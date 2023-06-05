import pytest
from graphql import graphql

from ariadne_graphql_proxy import set_resolver
from ariadne_graphql_proxy.cache import InMemoryCache, simple_cached_resolver


@pytest.fixture
def cache_backend():
    return InMemoryCache()


@pytest.fixture
def schema_with_simple_cached_resolver(schema, cache_backend):
    @simple_cached_resolver(cache_backend, "test_cache")
    def resolver(obj, info, **kwargs):
        info.context.append([obj, info, kwargs])
        if isinstance(obj, dict):
            return obj.get(info.field_name)
        return getattr(obj, info.field_name)

    set_resolver(schema, "Query", "basic", resolver)
    set_resolver(schema, "Query", "complex", resolver)
    return schema


@pytest.mark.asyncio
async def test_original_resolver_is_called_when_there_is_no_cache(
    schema_with_simple_cached_resolver, root_value
):
    context = []

    result = await graphql(
        schema_with_simple_cached_resolver,
        "{ basic }",
        root_value=root_value,
        context_value=context,
    )

    assert not result.errors
    assert len(context) == 1


@pytest.mark.asyncio
async def test_original_resolver_is_not_called_when_there_is_cache_for_it(
    schema_with_simple_cached_resolver, root_value
):
    context = []

    for _ in range(5):
        result = await graphql(
            schema_with_simple_cached_resolver,
            "{ basic }",
            root_value=root_value,
            context_value=context,
        )
        assert not result.errors

    assert len(context) == 1
