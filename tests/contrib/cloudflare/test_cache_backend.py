import json

import pytest

from ariadne_graphql_proxy.contrib.cloudflare import (
    CloudFlareCacheBackend,
    CloudFlareCacheBackendException,
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

    CloudFlareCacheBackend(
        account_id="acc_id",
        namespace_id="kv_id",
        api_email="email",
        api_key="key",
        base_url="https://base.url",
    )

    request = httpx_mock.get_request()
    assert (
        request.url
        == "https://base.url/accounts/acc_id/storage/kv/namespaces/kv_id/keys"
    )


def test_init_asserts_namespace_can_be_accessed_with_correct_headers(
    httpx_mock, list_keys_json
):
    httpx_mock.add_response(method="GET", status_code=200, json=list_keys_json)

    CloudFlareCacheBackend(
        account_id="acc_id",
        namespace_id="kv_id",
        api_email="email",
        api_key="key",
        base_url="https://base.url",
    )

    request = httpx_mock.get_request()
    assert request.headers["X-Auth-Email"] == "email"
    assert request.headers["X-Auth-Key"] == "key"


def test_init_raises_cloudflare_cache_backend_exception_for_unavailable_namespace(
    httpx_mock,
):
    not_found_json = {
        "result": None,
        "success": False,
        "errors": [{"code": 10013, "message": "list keys: 'namespace not found'"}],
        "messages": [],
    }
    httpx_mock.add_response(method="GET", status_code=404, json=not_found_json)

    with pytest.raises(CloudFlareCacheBackendException) as exc_info:
        CloudFlareCacheBackend(
            account_id="acc_id",
            namespace_id="kv_id",
            api_email="email",
            api_key="key",
            base_url="https://base.url",
        )

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
    cache = CloudFlareCacheBackend(
        account_id="acc_id",
        namespace_id="kv_id",
        api_email="email",
        api_key="key",
        base_url="https://base.url",
    )

    await cache.set("key", "value")

    request = httpx_mock.get_request(method="PUT")
    assert (
        request.url
        == "https://base.url/accounts/acc_id/storage/kv/namespaces/kv_id/values/key"
    )


@pytest.mark.asyncio
async def test_set_sends_request_with_correct_headers(httpx_mock, list_keys_json):
    httpx_mock.add_response(method="GET", status_code=200, json=list_keys_json)
    httpx_mock.add_response(method="PUT", status_code=200)
    cache = CloudFlareCacheBackend(
        account_id="acc_id",
        namespace_id="kv_id",
        api_email="email",
        api_key="key",
        base_url="https://base.url",
    )

    await cache.set("key", "value")

    request = httpx_mock.get_request(method="PUT")
    assert request.headers["X-Auth-Email"] == "email"
    assert request.headers["X-Auth-Key"] == "key"


@pytest.mark.asyncio
async def test_set_sends_correct_payload_to_cache_value(httpx_mock, list_keys_json):
    httpx_mock.add_response(method="GET", status_code=200, json=list_keys_json)
    httpx_mock.add_response(method="PUT", status_code=200)
    cache = CloudFlareCacheBackend(
        account_id="acc_id",
        namespace_id="kv_id",
        api_email="email",
        api_key="key",
        base_url="https://base.url",
    )

    await cache.set("key", "test_value")

    request = httpx_mock.get_request(method="PUT")
    assert {f.name: f.file for f in request.stream.fields} == {
        "value": json.dumps({"value": "test_value"}),
        "metadata": "{}",
    }


@pytest.mark.asyncio
async def test_set_sends_request_with_provided_ttl(httpx_mock, list_keys_json):
    httpx_mock.add_response(method="GET", status_code=200, json=list_keys_json)
    httpx_mock.add_response(method="PUT", status_code=200)
    cache = CloudFlareCacheBackend(
        account_id="acc_id",
        namespace_id="kv_id",
        api_email="email",
        api_key="key",
        base_url="https://base.url",
    )

    await cache.set("key", "value", 300)

    request = httpx_mock.get_request(method="PUT")
    assert request.url.params["expiration_ttl"] == "300"


@pytest.mark.asyncio
async def test_get_retrives_value_from_correct_url(httpx_mock, list_keys_json):
    httpx_mock.add_response(method="GET", status_code=200, json=list_keys_json)
    httpx_mock.add_response(method="GET", status_code=200, json={"value": "test_value"})
    cache = CloudFlareCacheBackend(
        account_id="acc_id",
        namespace_id="kv_id",
        api_email="email",
        api_key="key",
        base_url="https://base.url",
    )

    await cache.get("key")

    request = httpx_mock.get_requests()[-1]
    assert (
        request.url
        == "https://base.url/accounts/acc_id/storage/kv/namespaces/kv_id/values/key"
    )


@pytest.mark.asyncio
async def test_get_sends_request_with_correct_headers(httpx_mock, list_keys_json):
    httpx_mock.add_response(method="GET", status_code=200, json=list_keys_json)
    httpx_mock.add_response(method="GET", status_code=200, json={"value": "test_value"})
    cache = CloudFlareCacheBackend(
        account_id="acc_id",
        namespace_id="kv_id",
        api_email="email",
        api_key="key",
        base_url="https://base.url",
    )

    await cache.get("key")

    request = httpx_mock.get_requests()[-1]
    assert request.headers["X-Auth-Email"] == "email"
    assert request.headers["X-Auth-Key"] == "key"


@pytest.mark.asyncio
async def test_get_returns_retrieved_value(httpx_mock, list_keys_json):
    httpx_mock.add_response(method="GET", status_code=200, json=list_keys_json)
    httpx_mock.add_response(method="GET", status_code=200, json={"value": "test_value"})
    cache = CloudFlareCacheBackend(
        account_id="acc_id",
        namespace_id="kv_id",
        api_email="email",
        api_key="key",
        base_url="https://base.url",
    )

    value = await cache.get("key")

    assert value == "test_value"


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
    cache = CloudFlareCacheBackend(
        account_id="acc_id",
        namespace_id="kv_id",
        api_email="email",
        api_key="key",
        base_url="https://base.url",
    )

    value = await cache.get("key", "default")

    assert value == "default"
