import pytest
from httpx import Response

from ariadne_graphql_proxy import UpstreamGraphQLError, raise_upstream_error


def test_upstream_error_is_raised_from_text_response():
    response = Response(status_code=403, text="Forbidden")

    with pytest.raises(UpstreamGraphQLError) as exc_info:
        raise_upstream_error(response)

    assert exc_info.value.message == "Upstream service error"
    assert exc_info.value.extensions == {
        "upstream_response": {
            "status_code": 403,
            "content": "Forbidden",
        }
    }


def test_upstream_error_is_raised_from_json_response():
    response = Response(status_code=403, json={"detail": "Forbidden"})

    with pytest.raises(UpstreamGraphQLError) as exc_info:
        raise_upstream_error(response)

    assert exc_info.value.message == "Upstream service error"
    assert exc_info.value.extensions == {
        "upstream_response": {
            "status_code": 403,
            "json": {"detail": "Forbidden"},
        }
    }


def test_upstream_error_is_raised_from_graphql_response():
    response = Response(status_code=400, json={"errors": ["Error"]})

    with pytest.raises(UpstreamGraphQLError) as exc_info:
        raise_upstream_error(response)

    assert exc_info.value.message == "Upstream service error"
    assert exc_info.value.extensions == {
        "upstream_response": {
            "status_code": 400,
            "json": {"errors": ["Error"]},
        }
    }
