from typing import Any, Dict

from graphql import GraphQLError
from httpx import Response


class UpstreamGraphQLError(GraphQLError):
    pass


def raise_upstream_error(response: Response):
    upstream_response: Dict[str, Any] = {"status_code": response.status_code}
    try:
        content_type = str(response.headers.get("content-type") or "")
        if content_type.startswith("application/json"):
            upstream_response["json"] = response.json()
        else:
            upstream_response["content"] = response.text
    except Exception:
        upstream_response["body"] = response.content

    raise UpstreamGraphQLError(
        "Upstream service error",
        extensions={"upstream_response": upstream_response},
    )
