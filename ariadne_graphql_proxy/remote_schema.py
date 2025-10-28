import httpx
from graphql import (
    GraphQLSchema,
    build_client_schema,
    get_introspection_query,
)


def get_remote_schema(graphql_url: str, headers: dict | None = None) -> GraphQLSchema:
    response = httpx.post(
        graphql_url,
        headers=headers,
        json={
            "operationName": "IntrospectionQuery",
            "query": get_introspection_query(),
        },
    )

    response.raise_for_status()
    return build_client_schema(response.json()["data"])
