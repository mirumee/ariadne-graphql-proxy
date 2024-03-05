import json
from textwrap import dedent
from unittest.mock import ANY, Mock, call

import pytest
from graphql import parse, print_schema

from ariadne_graphql_proxy import ProxyRootValue, ProxySchema


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
    assert len(final_schema.type_map["Query"].fields) == 5
    assert "basic" in final_schema.type_map["Query"].fields
    assert "complex" in final_schema.type_map["Query"].fields
    assert "unionField" in final_schema.type_map["Query"].fields
    assert "other" in final_schema.type_map["Query"].fields
    assert "otherComplex" in final_schema.type_map["Query"].fields


def test_multiple_local_schemas_are_added_to_proxy(schema, complex_schema):
    proxy_schema = ProxySchema()
    proxy_schema.add_schema(schema)
    proxy_schema.add_schema(complex_schema)

    final_schema = proxy_schema.get_final_schema()
    assert print_schema(final_schema)
    assert len(final_schema.type_map["Query"].fields) == 3
    assert "basic" in final_schema.type_map["Query"].fields
    assert "complex" in final_schema.type_map["Query"].fields
    assert "unionField" in final_schema.type_map["Query"].fields


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
    assert len(final_schema.type_map["Query"].fields) == 3
    assert "basic" in final_schema.type_map["Query"].fields
    assert "complex" in final_schema.type_map["Query"].fields
    assert "unionField" in final_schema.type_map["Query"].fields


def test_remote_schema_is_requested_by_proxy_using_headers_dict(
    httpx_mock, schema, schema_json
):
    httpx_mock.add_response(json=schema_json)

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/", {"auth": "ok"})

    request = httpx_mock.get_requests(url="http://graphql.example.com/")[0]
    assert request.headers["auth"] == "ok"


def test_remote_schema_is_requested_by_proxy_using_headers_callable(
    httpx_mock, schema, schema_json
):
    get_headers = Mock(return_value={"auth": "ok"})
    httpx_mock.add_response(json=schema_json)

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/", get_headers)

    request = httpx_mock.get_requests(url="http://graphql.example.com/")[0]
    assert request.headers["auth"] == "ok"

    get_headers.assert_called_once_with(None)


def test_multiple_proxy_schemas_use_dedicated_headers_to_retrieve(
    httpx_mock, schema_json, complex_schema_json
):
    get_headers = Mock(return_value={"auth": "ok"})

    httpx_mock.add_response(json=schema_json)
    httpx_mock.add_response(json=complex_schema_json)

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/1/", get_headers)
    proxy_schema.add_remote_schema("http://graphql.example.com/2/", {"auth": "test"})

    final_schema = proxy_schema.get_final_schema()
    assert print_schema(final_schema)
    assert len(final_schema.type_map["Query"].fields) == 3
    assert "basic" in final_schema.type_map["Query"].fields
    assert "complex" in final_schema.type_map["Query"].fields
    assert "unionField" in final_schema.type_map["Query"].fields

    get_headers.assert_called_once_with(None)

    request_1 = httpx_mock.get_requests(url="http://graphql.example.com/1/")[0]
    assert request_1.headers["auth"] == "ok"

    request_2 = httpx_mock.get_requests(url="http://graphql.example.com/2/")[0]
    assert request_2.headers["auth"] == "test"


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


@pytest.mark.asyncio
async def test_proxy_schema_handles_union_queries(
    httpx_mock,
    schema_json,
    root_value,
):
    httpx_mock.add_response(
        url="http://graphql.example.com/",
        json=schema_json,
    )
    httpx_mock.add_response(
        url="http://graphql.example.com/",
        json={"data": root_value},
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/")
    proxy_schema.get_final_schema()

    await proxy_schema.root_resolver(
        {},
        "TestQuery",
        None,
        parse(
            """
            query TestQuery {
              unionField {
                ... on Shipping {
                  id
                  name
                }
                ... on Warehouse {
                  id
                  address
                }
              }
            }
            """
        ),
    )

    request = httpx_mock.get_requests(url="http://graphql.example.com/")[-1]
    assert json.loads(request.content) == {
        "operationName": "TestQuery",
        "variables": None,
        "query": dedent(
            """
            query TestQuery {
              unionField {
                ... on Shipping {
                  id
                  name
                }
                ... on Warehouse {
                  id
                  address
                }
              }
            }
            """
        ).strip(),
    }


@pytest.mark.asyncio
async def test_proxy_schema_handles_union_queries_with_fragments(
    httpx_mock,
    schema_json,
    root_value,
):
    httpx_mock.add_response(
        url="http://graphql.example.com/",
        json=schema_json,
    )
    httpx_mock.add_response(
        url="http://graphql.example.com/",
        json={"data": root_value},
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/")
    proxy_schema.get_final_schema()

    await proxy_schema.root_resolver(
        {},
        "TestQuery",
        None,
        parse(
            """
            fragment ShippingFields on Shipping {
              id
              name
            }

            fragment WarehouseFields on Warehouse {
              id
              address
            }

            query TestQuery {
              unionField {
                ... ShippingFields
                ... WarehouseFields
              }
            }
            """
        ),
    )

    request = httpx_mock.get_requests(url="http://graphql.example.com/")[-1]
    assert json.loads(request.content) == {
        "operationName": "TestQuery",
        "variables": None,
        "query": dedent(
            """
            query TestQuery {
              unionField {
                ... on Shipping {
                  id
                  name
                }
                ... on Warehouse {
                  id
                  address
                }
              }
            }
            """
        ).strip(),
    }


@pytest.mark.asyncio
async def test_proxy_schema_handles_omitted_optional_variables(
    httpx_mock,
    schema_json,
):
    httpx_mock.add_response(url="http://graphql.example.com/", json=schema_json)

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/")
    proxy_schema.get_final_schema()

    await proxy_schema.root_resolver(
        {},
        "TestQuery",
        {"arg": "test"},
        parse(
            """
            query TestQuery($arg: Generic, $other: Generic) {
              basic(arg: $arg, other: $other)
            }
            """
        ),
    )

    request = httpx_mock.get_requests(url="http://graphql.example.com/")[-1]
    assert json.loads(request.content) == {
        "operationName": "TestQuery",
        "variables": {"arg": "test"},
        "query": dedent(
            """
            query TestQuery($arg: Generic, $other: Generic) {
              basic(arg: $arg, other: $other)
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


@pytest.mark.asyncio
async def test_proxy_schema_includes_headers_dict_in_requests(
    httpx_mock,
    schema_json,
    root_value,
):
    httpx_mock.add_response(
        url="http://graphql.example.com/",
        json=schema_json,
    )
    httpx_mock.add_response(
        url="http://graphql.example.com/",
        json={"data": root_value},
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/", {"auth": "ok"})
    proxy_schema.get_final_schema()

    await proxy_schema.root_resolver(
        {},
        "TestQuery",
        None,
        parse("query TestQuery { basic }"),
    )

    request = httpx_mock.get_requests(url="http://graphql.example.com/")[-1]
    assert request.headers["auth"] == "ok"


@pytest.mark.asyncio
async def test_proxy_schema_includes_headers_from_callable_in_requests(
    httpx_mock,
    schema_json,
    root_value,
):
    get_headers = Mock(return_value={"auth": "test"})

    httpx_mock.add_response(
        url="http://graphql.example.com/",
        json=schema_json,
    )
    httpx_mock.add_response(
        url="http://graphql.example.com/",
        json={"data": root_value},
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/", get_headers)
    proxy_schema.get_final_schema()

    await proxy_schema.root_resolver(
        {},
        "TestQuery",
        None,
        parse("query TestQuery { basic }"),
    )

    request = httpx_mock.get_requests(url="http://graphql.example.com/")[-1]
    assert request.headers["auth"] == "test"

    get_headers.assert_has_calls(
        [
            call(None),
            call(ANY),
        ]
    )


@pytest.mark.asyncio
async def test_root_value_for_remote_schema_includes_proxied_errors(
    httpx_mock, schema_json
):
    httpx_mock.add_response(json=schema_json)
    httpx_mock.add_response(
        json={
            "errors": [
                {
                    "message": "Something bad has happened!",
                    "path": ["complex", "id"],
                },
            ],
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

    assert isinstance(root_value, ProxyRootValue)
    assert root_value.errors == [
        {
            "message": "Something bad has happened!",
            "path": ["remote_0", "complex", "id"],
        },
    ]


@pytest.mark.asyncio
async def test_root_value_for_remote_schema_excludes_errors(httpx_mock, schema_json):
    httpx_mock.add_response(json=schema_json)
    httpx_mock.add_response(
        json={
            "errors": [
                {
                    "message": "Something bad has happened!",
                    "path": ["complex", "id"],
                },
            ],
        }
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/", proxy_errors=False)

    proxy_schema.get_final_schema()
    root_value = await proxy_schema.root_resolver(
        {},
        "Query",
        None,
        parse("query Query { complex { id name } }"),
    )

    assert not isinstance(root_value, ProxyRootValue)
    assert root_value is None


@pytest.mark.asyncio
async def test_root_value_for_remote_schema_includes_proxied_extensions(
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
            "extensions": {
                "score": 100,
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

    assert isinstance(root_value, ProxyRootValue)
    assert root_value.root_value == {
        "complex": {
            "id": "123",
            "name": "Test",
        },
    }
    assert root_value.extensions == {
        "remote_0": {
            "score": 100,
        },
    }


@pytest.mark.asyncio
async def test_root_value_for_remote_schema_excludes_extensions(
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
            "extensions": {
                "score": 100,
            },
        }
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema(
        "http://graphql.example.com/", proxy_extensions=False
    )

    proxy_schema.get_final_schema()
    root_value = await proxy_schema.root_resolver(
        {},
        "Query",
        None,
        parse("query Query { complex { id name } }"),
    )

    assert not isinstance(root_value, ProxyRootValue)
    assert root_value == {
        "complex": {
            "id": "123",
            "name": "Test",
        },
    }
