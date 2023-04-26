import asyncio

from unittest.mock import Mock, AsyncMock

import pytest
from graphql import graphql

from ariadne_graphql_proxy import GraphQLProxyResolver, set_resolver, unset_resolver
from ariadne_graphql_proxy.cache import InMemoryCache

GRAPHQL_URL = "http://upstream.example.com/graphql/"


@pytest.fixture
def cache_backend():
    return InMemoryCache()


@pytest.mark.asyncio
async def test_proxy_resolver_proxies_its_query_branch(
    mocker,
    httpx_response,
    schema,
    root_value,
):
    resolver = GraphQLProxyResolver(url=GRAPHQL_URL)
    set_resolver(schema, "Query", "basic", resolver)

    # Use default resolver for complex field
    unset_resolver(schema, "Query", "complex")

    # Remove root value for basic field
    root_value.pop("basic")

    post_mock = AsyncMock(
        return_value=httpx_response({"data": {"basic": "Success"}}),
    )
    mocker.patch(
        "ariadne_graphql_proxy.graphql_proxy_resolver.AsyncClient.post", post_mock
    )

    result = await graphql(
        schema,
        "{ basic complex { id } }",
        root_value=root_value,
        context_value={"headers": {}},
    )

    assert not result.errors
    assert result.data == {
        "basic": "Success",
        "complex": {"id": "123"},
    }

    post_mock.assert_called_with(
        GRAPHQL_URL,
        headers=None,
        json={
            "operationName": None,
            "query": "query {\n  basic\n}",
            "variables": {},
        },
    )


@pytest.mark.asyncio
async def test_proxy_resolver_proxies_specified_headers(
    mocker,
    httpx_response,
    schema,
    root_value,
):
    resolver = GraphQLProxyResolver(
        url=GRAPHQL_URL,
        proxy_headers=["authorization"],
    )
    set_resolver(schema, "Query", "basic", resolver)

    # Use default resolver for complex field
    unset_resolver(schema, "Query", "complex")

    auth_header = "BEARER testtesttesttest"

    # Remove root value for basic field
    root_value.pop("basic")

    post_mock = AsyncMock(
        return_value=httpx_response({"data": {"basic": "Success"}}),
    )
    mocker.patch(
        "ariadne_graphql_proxy.graphql_proxy_resolver.AsyncClient.post", post_mock
    )

    result = await graphql(
        schema,
        "{ basic }",
        root_value=root_value,
        context_value={
            "headers": {
                "authorization": auth_header,
                "extra": "oh no",
            },
        },
    )

    assert not result.errors
    assert result.data == {"basic": "Success"}

    post_mock.assert_called_with(
        "http://upstream.example.com/graphql/",
        headers={"authorization": auth_header},
        json={
            "operationName": None,
            "query": "query {\n  basic\n}",
            "variables": {},
        },
    )


@pytest.mark.asyncio
async def test_proxy_resolver_proxies_headers_via_callable(
    mocker,
    httpx_response,
    schema,
    root_value,
):
    def proxy_headers(_, info, payload):
        return {
            "x-auth": info.context["headers"].get("authorization"),
        }

    resolver = GraphQLProxyResolver(
        url=GRAPHQL_URL,
        proxy_headers=proxy_headers,
    )
    set_resolver(schema, "Query", "basic", resolver)

    # Use default resolver for complex field
    unset_resolver(schema, "Query", "complex")

    auth_header = "BEARER testtesttesttest"

    # Remove root value for basic field
    root_value.pop("basic")

    post_mock = AsyncMock(
        return_value=httpx_response({"data": {"basic": "Success"}}),
    )
    mocker.patch(
        "ariadne_graphql_proxy.graphql_proxy_resolver.AsyncClient.post", post_mock
    )

    result = await graphql(
        schema,
        "{ basic }",
        root_value=root_value,
        context_value={
            "headers": {
                "authorization": auth_header,
                "extra": "oh no",
            },
        },
    )

    assert not result.errors
    assert result.data == {"basic": "Success"}

    post_mock.assert_called_with(
        "http://upstream.example.com/graphql/",
        headers={"x-auth": auth_header},
        json={
            "operationName": None,
            "query": "query {\n  basic\n}",
            "variables": {},
        },
    )


@pytest.mark.asyncio
async def test_proxy_resolver_with_cache_caches_result(
    mocker,
    httpx_response,
    cache_backend,
    schema,
    root_value,
):
    resolver = GraphQLProxyResolver(
        url=GRAPHQL_URL,
        cache=cache_backend,
    )
    set_resolver(schema, "Query", "basic", resolver)

    # Remove root value for basic field
    root_value.pop("basic")

    post_mock = Mock(
        status_code=200,
        headers={"content-type": "application/json"},
        json=Mock(
            return_value={"data": {"basic": "Success"}},
        ),
        return_value=httpx_response({"data": {"basic": "Success"}}),
    )
    mocker.patch(
        "ariadne_graphql_proxy.graphql_proxy_resolver.AsyncClient.post",
        return_value=post_mock,
    )

    result = await graphql(
        schema,
        "{ basic }",
        context_value={"headers": {}},
        root_value=root_value,
    )

    assert not result.errors
    assert result.data == {"basic": "Success"}

    result = await graphql(
        schema,
        "{ basic }",
        context_value={"headers": {}},
        root_value=root_value,
    )

    assert not result.errors
    assert result.data == {"basic": "Success"}

    post_mock.json.assert_called_once()


@pytest.mark.asyncio
async def test_proxy_resolver_caches_results_with_ttl(
    mocker,
    cache_backend,
    schema,
    root_value,
):
    resolver = GraphQLProxyResolver(
        url=GRAPHQL_URL,
        cache=cache_backend,
        cache_ttl=1,
    )
    set_resolver(schema, "Query", "basic", resolver)

    # Remove root value for basic field
    root_value.pop("basic")

    post_mock = Mock(
        status_code=200,
        headers={"content-type": "application/json"},
        json=Mock(
            return_value={"data": {"basic": "Success"}},
        ),
    )
    mocker.patch(
        "ariadne_graphql_proxy.graphql_proxy_resolver.AsyncClient.post",
        return_value=post_mock,
    )

    result = await graphql(
        schema,
        "{ basic }",
        context_value={"headers": {}},
        root_value=root_value,
    )

    assert not result.errors
    assert result.data == {"basic": "Success"}

    result = await graphql(
        schema,
        "{ basic }",
        context_value={"headers": {}},
        root_value=root_value,
    )

    assert not result.errors
    assert result.data == {"basic": "Success"}

    post_mock.json.assert_called_once()

    await asyncio.sleep(1)

    result = await graphql(
        schema,
        "{ basic }",
        context_value={"headers": {}},
        root_value=root_value,
    )

    assert not result.errors
    assert result.data == {"basic": "Success"}

    assert post_mock.json.call_count == 2


@pytest.mark.asyncio
async def test_proxy_resolver_handles_error_text_response(
    mocker,
    httpx_response,
    cache_backend,
    schema,
    root_value,
):
    resolver = GraphQLProxyResolver(
        url=GRAPHQL_URL,
        cache=cache_backend,
    )
    set_resolver(schema, "Query", "basic", resolver)

    # Remove root value for basic field
    root_value.pop("basic")

    mocker.patch(
        "ariadne_graphql_proxy.graphql_proxy_resolver.AsyncClient.post",
        return_value=httpx_response(text="Not available", status_code=400),
    )

    result = await graphql(
        schema,
        "{ basic }",
        context_value={"headers": {}},
        root_value=root_value,
    )

    assert result.errors
    assert result.errors[0].message == "Upstream service error"
    assert result.errors[0].extensions == {
        "upstream_response": {
            "status_code": 400,
            "content": "Not available",
        },
    }
    assert result.data == {"basic": None}


@pytest.mark.asyncio
async def test_proxy_resolver_handles_graphql_error_response(
    mocker,
    httpx_response,
    cache_backend,
    schema,
    root_value,
):
    resolver = GraphQLProxyResolver(
        url=GRAPHQL_URL,
        cache=cache_backend,
    )
    set_resolver(schema, "Query", "basic", resolver)

    # Remove root value for basic field
    root_value.pop("basic")

    mocker.patch(
        "ariadne_graphql_proxy.graphql_proxy_resolver.AsyncClient.post",
        return_value=httpx_response(json={"errors": ["invalid"]}, status_code=400),
    )

    result = await graphql(
        schema,
        "{ basic }",
        context_value={"headers": {}},
        root_value=root_value,
    )

    assert result.errors
    assert result.errors[0].message == "Upstream service error"
    assert result.errors[0].extensions == {
        "upstream_response": {
            "status_code": 400,
            "json": {"errors": ["invalid"]},
        },
    }
    assert result.data == {"basic": None}
