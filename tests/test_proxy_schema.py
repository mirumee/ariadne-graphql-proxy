import json
from textwrap import dedent

import pytest
from graphql import parse, print_schema

from ariadne_graphql_proxy import ProxySchema


def test_local_schema_is_added_to_proxy(schema):
    proxy_schema = ProxySchema()
    proxy_schema.add_schema(schema)

    final_schema = proxy_schema.get_final_schema()
    assert print_schema(final_schema) == print_schema(schema)


def test_remote_schema_is_added_to_proxy(httpx_mock, schema, schema_json):
    httpx_mock.add_response(json=schema_json)

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/")

    final_schema = proxy_schema.get_final_schema()
    assert print_schema(final_schema) == print_schema(schema)


def test_local_and_proxy_schemas_are_added_to_proxy(
    httpx_mock, schema, other_schema_json
):
    httpx_mock.add_response(json=other_schema_json)

    proxy_schema = ProxySchema()
    proxy_schema.add_schema(schema)
    proxy_schema.add_remote_schema("http://graphql.example.com/")

    final_schema = proxy_schema.get_final_schema()
    assert print_schema(final_schema)
    assert len(final_schema.type_map["Query"].fields) == 4
    assert "basic" in final_schema.type_map["Query"].fields
    assert "complex" in final_schema.type_map["Query"].fields
    assert "other" in final_schema.type_map["Query"].fields
    assert "otherComplex" in final_schema.type_map["Query"].fields


def test_multiple_local_schemas_are_added_to_proxy(schema, complex_schema):
    proxy_schema = ProxySchema()
    proxy_schema.add_schema(schema)
    proxy_schema.add_schema(complex_schema)

    final_schema = proxy_schema.get_final_schema()
    assert print_schema(final_schema)
    assert len(final_schema.type_map["Query"].fields) == 2
    assert "basic" in final_schema.type_map["Query"].fields
    assert "complex" in final_schema.type_map["Query"].fields


def test_multiple_proxy_schemas_are_added_to_proxy(
    httpx_mock, schema_json, complex_schema_json
):
    httpx_mock.add_response(json=schema_json)
    httpx_mock.add_response(json=complex_schema_json)

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/1/")
    proxy_schema.add_remote_schema("http://graphql.example.com/2/")

    final_schema = proxy_schema.get_final_schema()
    assert print_schema(final_schema)
    assert len(final_schema.type_map["Query"].fields) == 2
    assert "basic" in final_schema.type_map["Query"].fields
    assert "complex" in final_schema.type_map["Query"].fields


def test_local_schema_can_be_retrieved_from_proxy(schema):
    proxy_schema = ProxySchema()
    schema_id = proxy_schema.add_schema(schema)

    retrieved_schema = proxy_schema.get_sub_schema(schema_id)
    assert print_schema(retrieved_schema) == print_schema(schema)


def test_remote_schema_can_be_retrieved_from_proxy(httpx_mock, schema, schema_json):
    httpx_mock.add_response(json=schema_json)

    proxy_schema = ProxySchema()
    schema_id = proxy_schema.add_remote_schema("http://graphql.example.com/")

    retrieved_schema = proxy_schema.get_sub_schema(schema_id)
    assert print_schema(retrieved_schema) == print_schema(schema)


@pytest.mark.asyncio
async def test_root_value_is_not_retrieved_for_local_schema(schema):
    proxy_schema = ProxySchema()
    proxy_schema.add_schema(schema)

    proxy_schema.get_final_schema()
    root_value = await proxy_schema.root_resolver(
        {},
        "Query",
        None,
        parse("query Query { basic }"),
    )

    assert root_value is None


@pytest.mark.asyncio
async def test_custom_root_value_is_supported(schema):
    proxy_schema = ProxySchema({"root": "test"})
    proxy_schema.add_schema(schema)

    proxy_schema.get_final_schema()
    root_value = await proxy_schema.root_resolver(
        {},
        "Query",
        None,
        parse("query Query { basic }"),
    )

    assert root_value == {"root": "test"}


@pytest.mark.asyncio
async def test_custom_root_value_callable_supported(schema):
    def get_root_value(*_):
        return {"root": "sync"}

    proxy_schema = ProxySchema(get_root_value)
    proxy_schema.add_schema(schema)

    proxy_schema.get_final_schema()
    root_value = await proxy_schema.root_resolver(
        {},
        "Query",
        None,
        parse("query Query { basic }"),
    )

    assert root_value == {"root": "sync"}


@pytest.mark.asyncio
async def test_custom_root_value_async_callable_supported(schema):
    async def get_root_value(*_):
        return {"root": "async"}

    proxy_schema = ProxySchema(get_root_value)
    proxy_schema.add_schema(schema)

    proxy_schema.get_final_schema()
    root_value = await proxy_schema.root_resolver(
        {},
        "Query",
        None,
        parse("query Query { basic }"),
    )

    assert root_value == {"root": "async"}


@pytest.mark.asyncio
async def test_root_value_for_remote_schema_fields_is_retrieved_from_upstream(
    httpx_mock, schema_json
):
    httpx_mock.add_response(json=schema_json)
    httpx_mock.add_response(
        json={
            "data": {
                "complex": {
                    "id": "123",
                    "name": "Test",
                },
            },
        }
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/")

    proxy_schema.get_final_schema()
    root_value = await proxy_schema.root_resolver(
        {},
        "Query",
        None,
        parse("query Query { complex { id name } }"),
    )

    assert root_value == {
        "complex": {
            "id": "123",
            "name": "Test",
        },
    }


@pytest.mark.asyncio
async def test_root_value_for_separate_remote_schemas_is_retrieved_from_upstream(
    httpx_mock, schema_json, other_schema_json
):
    httpx_mock.add_response(url="http://graphql.example.com/1/", json=schema_json)
    httpx_mock.add_response(url="http://graphql.example.com/2/", json=other_schema_json)
    httpx_mock.add_response(
        url="http://graphql.example.com/1/",
        json={
            "data": {
                "complex": {
                    "id": "123",
                    "name": "Test",
                },
            },
        },
    )
    httpx_mock.add_response(
        url="http://graphql.example.com/2/",
        json={
            "data": {
                "otherComplex": {
                    "id": "321",
                    "name": "Other",
                    "group": {
                        "id": "653",
                    },
                },
            },
        },
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/1/")
    proxy_schema.add_remote_schema("http://graphql.example.com/2/")

    proxy_schema.get_final_schema()
    root_value = await proxy_schema.root_resolver(
        {},
        "Query",
        None,
        parse(
            """
            query Query {
              complex {
                id
                name
              }
              otherComplex {
                id
                name
                group {
                  id
                }
              } 
            }
            """
        ),
    )

    assert root_value == {
        "complex": {
            "id": "123",
            "name": "Test",
        },
        "otherComplex": {
            "id": "321",
            "name": "Other",
            "group": {
                "id": "653",
            },
        },
    }

    first_request = httpx_mock.get_requests(url="http://graphql.example.com/1/")[-1]
    assert json.loads(first_request.content) == {
        "operationName": "Query",
        "variables": None,
        "query": dedent(
            """
            query Query {
              complex {
                id
                name
              }
            }
            """
        ).strip(),
    }

    second_request = httpx_mock.get_requests(url="http://graphql.example.com/2/")[-1]
    assert json.loads(second_request.content) == {
        "operationName": "Query",
        "variables": None,
        "query": dedent(
            """
            query Query {
              otherComplex {
                id
                name
                group {
                  id
                }
              }
            }
            """
        ).strip(),
    }


@pytest.mark.asyncio
async def test_root_value_for_foreign_key_field_swaps_query_content_with_id(
    httpx_mock, schema_json, other_schema_json
):
    httpx_mock.add_response(url="http://graphql.example.com/1/", json=schema_json)
    httpx_mock.add_response(url="http://graphql.example.com/2/", json=other_schema_json)
    httpx_mock.add_response(
        url="http://graphql.example.com/1/",
        json={
            "data": {
                "complex": {
                    "id": "123",
                    "name": "Test",
                },
            },
        },
    )
    httpx_mock.add_response(
        url="http://graphql.example.com/2/",
        json={
            "data": {
                "otherComplex": {
                    "id": "321",
                    "name": "Other",
                    "group": {
                        "id": "653",
                    },
                },
            },
        },
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/1/")
    proxy_schema.add_remote_schema("http://graphql.example.com/2/")
    proxy_schema.add_foreign_key("OtherComplex", "group", "id")

    proxy_schema.get_final_schema()
    root_value = await proxy_schema.root_resolver(
        {},
        "Query",
        None,
        parse(
            """
            query Query {
              complex {
                id
                name
              }
              otherComplex {
                id
                name
                group {
                  name
                  rank
                }
              } 
            }
            """
        ),
    )

    assert root_value == {
        "complex": {
            "id": "123",
            "name": "Test",
        },
        "otherComplex": {
            "id": "321",
            "name": "Other",
            "group": {
                "id": "653",
            },
        },
    }

    first_request = httpx_mock.get_requests(url="http://graphql.example.com/1/")[-1]
    assert json.loads(first_request.content) == {
        "operationName": "Query",
        "variables": None,
        "query": dedent(
            """
            query Query {
              complex {
                id
                name
              }
            }
            """
        ).strip(),
    }

    second_request = httpx_mock.get_requests(url="http://graphql.example.com/2/")[-1]
    assert json.loads(second_request.content) == {
        "operationName": "Query",
        "variables": None,
        "query": dedent(
            """
            query Query {
              otherComplex {
                id
                name
                group {
                  id
                }
              }
            }
            """
        ).strip(),
    }


@pytest.mark.asyncio
async def test_root_value_excludes_delayed_field(httpx_mock, schema_json):
    httpx_mock.add_response(json=schema_json)
    httpx_mock.add_response(
        url="http://graphql.example.com/1/",
        json={
            "data": {
                "basic": "I'm in!",
            },
        },
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/1/")
    proxy_schema.add_delayed_fields({"Query": ["complex"]})

    proxy_schema.get_final_schema()
    root_value = await proxy_schema.root_resolver(
        {},
        "Query",
        None,
        parse(
            """
            query Query {
              basic
            }
            """
        ),
    )

    assert root_value == {"basic": "I'm in!"}


@pytest.mark.asyncio
async def test_proxy_schema_splits_queries_inline_fragments_between_schemas(
    httpx_mock,
    search_schema_json,
    search_root_value,
    store_schema_json,
):
    httpx_mock.add_response(
        url="http://graphql.example.com/search/", json=search_schema_json
    )
    httpx_mock.add_response(
        url="http://graphql.example.com/store/", json=store_schema_json
    )
    httpx_mock.add_response(
        url="http://graphql.example.com/search/",
        json={"data": search_root_value},
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/search/")
    proxy_schema.add_remote_schema("http://graphql.example.com/store/")

    proxy_schema.get_final_schema()
    root_value = await proxy_schema.root_resolver(
        {},
        "Query",
        None,
        parse(
            """
            query Query {
              search(query: "test") {
                ... on User {
                    id
                    url
                    username
                }
                ... on Order {
                    id
                    url
                    customer
                }
              }
            }
            """
        ),
    )

    assert root_value == {
        "search": [
            {
                "__typename": "User",
                "url": "/u/aerith/3/",
                "id": "3",
                "username": "Aerith",
                "email": "aerith@example.com",
            },
            {
                "__typename": "Order",
                "id": "5s87d6sa85f7asds",
                "url": "/o/5s87d6sa85f7asds/",
            },
            {
                "__typename": "User",
                "url": "/u/bob/7/",
                "id": "7",
                "username": "Bob",
                "email": "bob@example.com",
            },
        ],
    }

    first_request = httpx_mock.get_requests(url="http://graphql.example.com/search/")[
        -1
    ]
    assert json.loads(first_request.content) == {
        "operationName": "Query",
        "variables": None,
        "query": dedent(
            """
            query Query {
              search(query: \"test\") {
                ... on User {
                  id
                  url
                  username
                }
                ... on Order {
                  id
                  url
                }
              }
            }
            """
        ).strip(),
    }

    store_requests = httpx_mock.get_requests(url="http://graphql.example.com/store/")
    assert len(store_requests) == 1


@pytest.mark.asyncio
async def test_proxy_schema_unpacks_fragment_in_query(
    httpx_mock,
    search_schema_json,
    search_root_value,
):
    httpx_mock.add_response(
        url="http://graphql.example.com/search/", json=search_schema_json
    )
    httpx_mock.add_response(
        url="http://graphql.example.com/search/",
        json={"data": search_root_value},
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/search/")
    proxy_schema.get_final_schema()

    await proxy_schema.root_resolver(
        {},
        "TestQuery",
        None,
        parse(
            """
            query TestQuery {
              search(query: "test") {
                ...resultFragment
              }
            }

            fragment resultFragment on Result {
              id
              url
            }
            """
        ),
    )

    request = httpx_mock.get_requests()[-1]
    assert json.loads(request.content) == {
        "operationName": "TestQuery",
        "variables": None,
        "query": dedent(
            """
            query TestQuery {
              search(query: "test") {
                id
                url
              }
            }
            """
        ).strip(),
    }


@pytest.mark.asyncio
async def test_proxy_schema_splits_variables_between_schemas(
    httpx_mock,
    search_schema_json,
    store_schema_json,
    search_root_value,
    store_root_value,
):
    httpx_mock.add_response(
        url="http://graphql.example.com/search/", json=search_schema_json
    )
    httpx_mock.add_response(
        url="http://graphql.example.com/store/", json=store_schema_json
    )
    httpx_mock.add_response(
        url="http://graphql.example.com/search/",
        json={"data": search_root_value},
    )
    httpx_mock.add_response(
        url="http://graphql.example.com/store/",
        json={"data": store_root_value},
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/search/")
    proxy_schema.add_remote_schema("http://graphql.example.com/store/")
    proxy_schema.get_final_schema()

    await proxy_schema.root_resolver(
        {},
        "TestQuery",
        {"searchQuery": "test", "orderId": "testId"},
        parse(
            """
            query TestQuery($searchQuery: String!, $orderId: ID!) {
              search(query: $searchQuery) {
                id
              }
              order(id: $orderId) {
                id
              }
            }
            """
        ),
    )

    search_request = httpx_mock.get_requests(url="http://graphql.example.com/search/")[
        -1
    ]
    store_request = httpx_mock.get_requests(url="http://graphql.example.com/store/")[-1]

    assert json.loads(search_request.content) == {
        "operationName": "TestQuery",
        "variables": {"searchQuery": "test"},
        "query": dedent(
            """
            query TestQuery($searchQuery: String!) {
              search(query: $searchQuery) {
                id
              }
            }
            """
        ).strip(),
    }
    assert json.loads(store_request.content) == {
        "operationName": "TestQuery",
        "variables": {"orderId": "testId"},
        "query": dedent(
            """
            query TestQuery($orderId: ID!) {
              order(id: $orderId) {
                id
              }
            }
            """
        ).strip(),
    }


@pytest.mark.asyncio
async def test_proxy_schema_splits_variables_from_fragments_between_schemas(
    httpx_mock,
    search_schema_json,
    store_schema_json,
    search_root_value,
    store_root_value,
):
    httpx_mock.add_response(
        url="http://graphql.example.com/search/", json=search_schema_json
    )
    httpx_mock.add_response(
        url="http://graphql.example.com/store/", json=store_schema_json
    )
    httpx_mock.add_response(
        url="http://graphql.example.com/search/",
        json={"data": search_root_value},
    )
    httpx_mock.add_response(
        url="http://graphql.example.com/store/",
        json={"data": store_root_value},
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/search/")
    proxy_schema.add_remote_schema("http://graphql.example.com/store/")
    proxy_schema.get_final_schema()

    await proxy_schema.root_resolver(
        {},
        "TestQuery",
        {"searchQuery": "test", "orderId": "testId"},
        parse(
            """
            query TestQuery($searchQuery: String!, $orderId: ID!) {
              ...searchFragment
              ...orderFragment
            }

            fragment searchFragment on Query {
              search(query: $searchQuery) {
                id
              }
            }

            fragment orderFragment on Query {
              order(id: $orderId) {
                id
              }
            }
            """
        ),
    )

    search_request = httpx_mock.get_requests(url="http://graphql.example.com/search/")[
        -1
    ]
    store_request = httpx_mock.get_requests(url="http://graphql.example.com/store/")[-1]

    assert json.loads(search_request.content) == {
        "operationName": "TestQuery",
        "variables": {"searchQuery": "test"},
        "query": dedent(
            """
            query TestQuery($searchQuery: String!) {
              search(query: $searchQuery) {
                id
              }
            }
            """
        ).strip(),
    }
    assert json.loads(store_request.content) == {
        "operationName": "TestQuery",
        "variables": {"orderId": "testId"},
        "query": dedent(
            """
            query TestQuery($orderId: ID!) {
              order(id: $orderId) {
                id
              }
            }
            """
        ).strip(),
    }


def test_insert_field_adds_field_into_local_schemas_with_given_type(
    schema, complex_schema
):
    proxy_schema = ProxySchema()
    proxy_schema.add_schema(schema)
    proxy_schema.add_schema(complex_schema)

    proxy_schema.insert_field("Complex", "newField: String!")

    assert proxy_schema.get_sub_schema(0).type_map["Complex"].fields["newField"]
    assert proxy_schema.get_sub_schema(1).type_map["Complex"].fields["newField"]


def test_insert_field_adds_field_into_remote_schemas_with_given_type(
    httpx_mock, schema_json, complex_schema_json
):
    httpx_mock.add_response(url="http://graphql.example.com/schema/", json=schema_json)
    httpx_mock.add_response(
        url="http://graphql.example.com/complex_schema/", json=complex_schema_json
    )
    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/schema/")
    proxy_schema.add_remote_schema("http://graphql.example.com/complex_schema/")

    proxy_schema.insert_field("Complex", "newField: String!")

    assert proxy_schema.get_sub_schema(0).type_map["Complex"].fields["newField"]
    assert proxy_schema.get_sub_schema(1).type_map["Complex"].fields["newField"]


def test_insert_field_adds_field_into_both_local_and_remote_schema(
    httpx_mock, schema, complex_schema_json
):
    httpx_mock.add_response(
        url="http://graphql.example.com/complex_schema/", json=complex_schema_json
    )
    proxy_schema = ProxySchema()
    proxy_schema.add_schema(schema)
    proxy_schema.add_remote_schema("http://graphql.example.com/complex_schema/")

    proxy_schema.insert_field("Complex", "newField: String!")

    assert proxy_schema.get_sub_schema(0).type_map["Complex"].fields["newField"]
    assert proxy_schema.get_sub_schema(1).type_map["Complex"].fields["newField"]
