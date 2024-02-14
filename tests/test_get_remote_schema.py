import pytest
from graphql import print_schema
from httpx import HTTPStatusError

from ariadne_graphql_proxy import get_remote_schema


def test_remote_schema_document_is_returned(httpx_mock, schema, schema_json):
    httpx_mock.add_response(json=schema_json)
    remote_schema = get_remote_schema("http://graphql.example.com/")
    assert remote_schema
    assert print_schema(remote_schema) == print_schema(schema)


def test_remote_schema_document_is_retrieved_with_headers_dict(
    httpx_mock, schema, schema_json
):
    httpx_mock.add_response(json=schema_json)
    remote_schema = get_remote_schema("http://graphql.example.com/", {"auth": "ok"})
    assert remote_schema
    assert print_schema(remote_schema) == print_schema(schema)

    request = httpx_mock.get_requests(url="http://graphql.example.com/")[0]
    assert request.headers["auth"] == "ok"


def test_remote_schema_fetch_raises_http_response_error(httpx_mock):
    httpx_mock.add_response(status_code=404, text="Not found")

    with pytest.raises(HTTPStatusError):
        get_remote_schema("http://graphql.example.com/")
