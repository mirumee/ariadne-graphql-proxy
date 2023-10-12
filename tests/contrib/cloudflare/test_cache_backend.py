import json
from typing import Any

import pytest

from ariadne_graphql_proxy.cache import CacheSerializer
from ariadne_graphql_proxy.contrib.cloudflare import (
    CloudflareCacheBackend,
    CloudflareCacheError,
)


@pytest.fixture
def list_keys_json():
    return {
        "errors": [],
        "messages": [],
        "result": [{"metadata": {}, "name": "key_name"}],
        "success": True,
        "result_info": {"count": 1, "cursor": "abcd"},
    }


def test_init_asserts_namespace_can_be_accessed_with_correct_url(
    httpx_mock, list_keys_json
):
    httpx_mock.add_response(method="GET", status_code=200, json=list_keys_json)

    CloudflareCacheBackend(
        account_id="acc_id", namespace_id="kv_id", base_url="https://base.url"
    )

    request = httpx_mock.get_request()
    assert (
        request.url
        == "https://base.url/accounts/acc_id/storage/kv/namespaces/kv_id/keys"
    )


@pytest.mark.parametrize(
    "headers",
    (
        {"X-Auth-Email": "email", "X-Auth-Key": "key"},
        {"Authorization": "Bearer abcd"},
    ),
)
def test_init_asserts_namespace_can_be_accessed_with_correct_headers(
    headers, httpx_mock, list_keys_json
):
    httpx_mock.add_response(method="GET", status_code=200, json=list_keys_json)

    CloudflareCacheBackend(account_id="acc_id", namespace_id="kv_id", headers=headers)

    request = httpx_mock.get_request()
    assert all(request.headers[key] == headers[key] for key in headers.keys())


def test_init_raises_cloudflare_cache_error_for_unavailable_namespace(httpx_mock):
    not_found_json = {
        "result": None,
        "success": False,
        "errors": [{"code": 10013, "message": "list keys: 'namespace not found'"}],
        "messages": [],
    }
    httpx_mock.add_response(method="GET", status_code=404, json=not_found_json)

    with pytest.raises(CloudflareCacheError) as exc_info:
        CloudflareCacheBackend(account_id="acc_id", namespace_id="kv_id")

    request = httpx_mock.get_request()
    assert exc_info.value.response
    exc_msg = str(exc_info.value)
    assert str(request.url) in exc_msg
    assert "404" in exc_msg
    assert str(json.dumps(not_found_json).encode("utf-8")) in exc_msg


@pytest.mark.asyncio
async def test_set_sends_request_to_correct_url(httpx_mock, list_keys_json):
    httpx_mock.add_response(method="GET", status_code=200, json=list_keys_json)
    httpx_mock.add_response(method="PUT", status_code=200)
    cache = CloudflareCacheBackend(
        account_id="acc_id", namespace_id="kv_id", base_url="https://base.url"
    )

    await cache.set("key", "value")

    request = httpx_mock.get_request(method="PUT")
    assert (
        request.url
        == "https://base.url/accounts/acc_id/storage/kv/namespaces/kv_id/values/key"
    )


@pytest.mark.parametrize(
    "headers",
    (
        {"X-Auth-Email": "email", "X-Auth-Key": "key"},
        {"Authorization": "Bearer abcd"},
    ),
)
@pytest.mark.asyncio
async def test_set_sends_request_with_correct_headers(
    headers, httpx_mock, list_keys_json
):
    httpx_mock.add_response(method="GET", status_code=200, json=list_keys_json)
    httpx_mock.add_response(method="PUT", status_code=200)
    cache = CloudflareCacheBackend(
        account_id="acc_id", namespace_id="kv_id", headers=headers
    )

    await cache.set("key", "value")

    request = httpx_mock.get_request(method="PUT")
    assert all(request.headers[key] == headers[key] for key in headers.keys())


@pytest.mark.asyncio
async def test_set_sends_correct_payload_to_cache_value(httpx_mock, list_keys_json):
    httpx_mock.add_response(method="GET", status_code=200, json=list_keys_json)
    httpx_mock.add_response(method="PUT", status_code=200)
    cache = CloudflareCacheBackend(account_id="acc_id", namespace_id="kv_id")

    await cache.set("key", "test_value")

    request = httpx_mock.get_request(method="PUT")
    assert {f.name: f.file for f in request.stream.fields} == {
        "value": cache.serializer.serialize("test_value"),
        "metadata": "{}",
    }


@pytest.mark.asyncio
async def test_set_uses_custom_serializer(httpx_mock, list_keys_json):
    httpx_mock.add_response(method="GET", status_code=200, json=list_keys_json)
    httpx_mock.add_response(method="PUT", status_code=200)

    class CustomSerializer(CacheSerializer):
        def serialize(self, value: Any) -> str:
            return str(value) + "-serialized"

    cache = CloudflareCacheBackend(
        account_id="acc_id", namespace_id="kv_id", serializer=CustomSerializer()
    )

    await cache.set("key", "test_value")

    request = httpx_mock.get_request(method="PUT")
    assert {f.name: f.file for f in request.stream.fields} == {
        "value": "test_value-serialized",
        "metadata": "{}",
    }


@pytest.mark.asyncio
async def test_set_sends_request_with_provided_ttl(httpx_mock, list_keys_json):
    httpx_mock.add_response(method="GET", status_code=200, json=list_keys_json)
    httpx_mock.add_response(method="PUT", status_code=200)
    cache = CloudflareCacheBackend(account_id="acc_id", namespace_id="kv_id")

    await cache.set("key", "value", 300)

    request = httpx_mock.get_request(method="PUT")
    assert request.url.params["expiration_ttl"] == "300"


@pytest.mark.asyncio
async def test_get_retrives_value_from_correct_url(httpx_mock, list_keys_json):
    httpx_mock.add_response(method="GET", status_code=200, json=list_keys_json)
    httpx_mock.add_response(method="GET", status_code=200, content=b'"test_value"')
    cache = CloudflareCacheBackend(
        account_id="acc_id", namespace_id="kv_id", base_url="https://base.url"
    )

    await cache.get("key")

    request = httpx_mock.get_requests()[-1]
    assert (
        request.url
        == "https://base.url/accounts/acc_id/storage/kv/namespaces/kv_id/values/key"
    )


@pytest.mark.parametrize(
    "headers",
    (
        {"X-Auth-Email": "email", "X-Auth-Key": "key"},
        {"Authorization": "Bearer abcd"},
    ),
)
@pytest.mark.asyncio
async def test_get_sends_request_with_correct_headers(
    headers, httpx_mock, list_keys_json
):
    httpx_mock.add_response(method="GET", status_code=200, json=list_keys_json)
    httpx_mock.add_response(method="GET", status_code=200, content=b'"test_value"')
    cache = CloudflareCacheBackend(
        account_id="acc_id", namespace_id="kv_id", headers=headers
    )

    await cache.get("key")

    request = httpx_mock.get_requests()[-1]
    assert all(request.headers[key] == headers[key] for key in headers.keys())


@pytest.mark.asyncio
async def test_get_returns_retrieved_value(httpx_mock, list_keys_json):
    httpx_mock.add_response(method="GET", status_code=200, json=list_keys_json)
    httpx_mock.add_response(method="GET", status_code=200, content=b'"test_value"')
    cache = CloudflareCacheBackend(account_id="acc_id", namespace_id="kv_id")

    value = await cache.get("key")

    assert value == "test_value"


@pytest.mark.asyncio
async def test_get_uses_custom_serializer(httpx_mock, list_keys_json):
    httpx_mock.add_response(method="GET", status_code=200, json=list_keys_json)
    httpx_mock.add_response(method="GET", status_code=200, content=b'"test_value"')

    class CustomSerializer(CacheSerializer):
        def deserialize(self, value: str) -> Any:
            return value.strip("'\"") + "-deserialized"

    cache = CloudflareCacheBackend(
        account_id="acc_id", namespace_id="kv_id", serializer=CustomSerializer()
    )

    value = await cache.get("key")

    assert value == "test_value-deserialized"


@pytest.mark.asyncio
async def test_get_returns_default_value_for_404_response(httpx_mock, list_keys_json):
    httpx_mock.add_response(method="GET", status_code=200, json=list_keys_json)
    httpx_mock.add_response(
        method="GET",
        status_code=404,
        json={
            "result": None,
            "success": False,
            "errors": [{"code": 10009, "message": "get: 'key not found'"}],
            "messages": [],
        },
    )
    cache = CloudflareCacheBackend(account_id="acc_id", namespace_id="kv_id")

    value = await cache.get("key", "default")

    assert value == "default"
