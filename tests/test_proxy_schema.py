import json
from textwrap import dedent
from unittest.mock import ANY, Mock, call

import pytest
from graphql import GraphQLObjectType, parse, print_schema

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
async def test_proxy_schema_handles_object_variables_correctly(
    httpx_mock,
    car_schema_json,
    car_root_value,
):
    httpx_mock.add_response(
        url="http://graphql.example.com/cars/", json=car_schema_json
    )
    httpx_mock.add_response(
        url="http://graphql.example.com/cars/",
        json={"data": car_root_value["carsByCriteria"]},
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/cars/")
    proxy_schema.get_final_schema()

    await proxy_schema.root_resolver(
        {},
        "CarsByCriteriaQuery",
        {"criteria": {"make": "Toyota", "model": "Corolla", "year": 2020}},
        parse(
            """
            query CarsByCriteriaQuery($criteria: SearchCriteria!) {
              carsByCriteria(input: { criteria: $criteria }) {
                id
                make
                model
                year
              }
            }
            """
        ),
    )

    cars_request = httpx_mock.get_requests(url="http://graphql.example.com/cars/")[-1]

    assert json.loads(cars_request.content) == {
        "operationName": "CarsByCriteriaQuery",
        "variables": {"criteria": {"make": "Toyota", "model": "Corolla", "year": 2020}},
        "query": dedent(
            """
            query CarsByCriteriaQuery($criteria: SearchCriteria!) {
              carsByCriteria(input: {criteria: $criteria}) {
                id
                make
                model
                year
              }
            }
            """
        ).strip(),
    }


@pytest.mark.asyncio
async def test_proxy_schema_handles_list_variables_correctly(
    httpx_mock,
    car_schema_json,
    car_root_value,
):
    httpx_mock.add_response(
        url="http://graphql.example.com/cars/", json=car_schema_json
    )
    httpx_mock.add_response(
        url="http://graphql.example.com/cars/",
        json={"data": car_root_value["carsByIds"]},
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/cars/")
    proxy_schema.get_final_schema()

    await proxy_schema.root_resolver(
        {},
        "CarsQuery",
        {"id": "car2"},
        parse(
            """
            query CarsQuery($id: ID!) {
              carsByIds(ids: [$id]) {
                id
                make
                model
                year
              }
            }
            """
        ),
    )

    cars_request = httpx_mock.get_requests(url="http://graphql.example.com/cars/")[-1]

    assert json.loads(cars_request.content) == {
        "operationName": "CarsQuery",
        "variables": {"id": "car2"},
        "query": dedent(
            """
            query CarsQuery($id: ID!) {
              carsByIds(ids: [$id]) {
                id
                make
                model
                year
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
    httpx_mock.add_response(url="http://graphql.example.com/", json={"data": {}})
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


@pytest.mark.asyncio
async def test_add_field_dependencies_for_nonexisting_schema_raises_error(
    httpx_mock, schema_json
):
    httpx_mock.add_response(json=schema_json)

    proxy_schema = ProxySchema()
    schema_id = proxy_schema.add_remote_schema("http://graphql.example.com/")

    with pytest.raises(ValueError) as exc_info:
        proxy_schema.add_field_dependencies(
            schema_id + 1, "Complex", "invalid", "{ group { name } }"
        )

    assert "Schema with ID '1' doesn't exist." == str(exc_info.value)


@pytest.mark.asyncio
async def test_add_field_dependencies_for_local_schema_raises_error(schema):
    proxy_schema = ProxySchema()
    schema_id = proxy_schema.add_schema(schema)

    with pytest.raises(ValueError) as exc_info:
        proxy_schema.add_field_dependencies(
            schema_id, "Complex", "invalid", "{ group { name } }"
        )

    assert "Schema with ID '0' is not a remote schema." == str(exc_info.value)


@pytest.mark.asyncio
async def test_add_field_dependencies_for_query_field_raises_error(
    httpx_mock, schema_json
):
    httpx_mock.add_response(json=schema_json)

    proxy_schema = ProxySchema()
    schema_id = proxy_schema.add_remote_schema("http://graphql.example.com/")

    with pytest.raises(ValueError) as exc_info:
        proxy_schema.add_field_dependencies(schema_id, "Query", "basic", "{ complex }")

    assert "Defining field dependencies for Query fields is not allowed." == str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_add_field_dependencies_for_mutation_field_raises_error(
    httpx_mock, schema_json
):
    httpx_mock.add_response(json=schema_json)

    proxy_schema = ProxySchema()
    schema_id = proxy_schema.add_remote_schema("http://graphql.example.com/")

    with pytest.raises(ValueError) as exc_info:
        proxy_schema.add_field_dependencies(
            schema_id, "Mutation", "basic", "{ complex }"
        )

    assert "Defining field dependencies for Mutation fields is not allowed." == str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_add_field_dependencies_for_subscription_field_raises_error(
    httpx_mock, schema_json
):
    httpx_mock.add_response(json=schema_json)

    proxy_schema = ProxySchema()
    schema_id = proxy_schema.add_remote_schema("http://graphql.example.com/")

    with pytest.raises(ValueError) as exc_info:
        proxy_schema.add_field_dependencies(
            schema_id, "Subscription", "basic", "{ complex }"
        )

    assert "Defining field dependencies for Subscription fields is not allowed." == str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_add_field_dependencies_for_nonexisting_type_raises_error(
    httpx_mock, schema_json
):
    httpx_mock.add_response(json=schema_json)

    proxy_schema = ProxySchema()
    schema_id = proxy_schema.add_remote_schema("http://graphql.example.com/")

    with pytest.raises(ValueError) as exc_info:
        proxy_schema.add_field_dependencies(
            schema_id, "Invalid", "basic", "{ complex }"
        )

    assert "Type 'Invalid' doesn't exist in schema with ID '0'." == str(exc_info.value)


@pytest.mark.asyncio
async def test_add_field_dependencies_for_invalid_type_raises_error(
    httpx_mock, schema_json
):
    httpx_mock.add_response(json=schema_json)

    proxy_schema = ProxySchema()
    schema_id = proxy_schema.add_remote_schema("http://graphql.example.com/")

    with pytest.raises(ValueError) as exc_info:
        proxy_schema.add_field_dependencies(
            schema_id, "InputType", "invalid", "{ group { name } }"
        )

    assert "Type 'InputType' in schema with ID '0' is not an object type." == str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_add_field_dependencies_for_nonexisting_type_field_raises_error(
    httpx_mock, schema_json
):
    httpx_mock.add_response(json=schema_json)

    proxy_schema = ProxySchema()
    schema_id = proxy_schema.add_remote_schema("http://graphql.example.com/")

    with pytest.raises(ValueError) as exc_info:
        proxy_schema.add_field_dependencies(
            schema_id, "Complex", "invalid", "{ group { name } }"
        )

    assert (
        "Type 'Complex' doesn't define the 'invalid' field in any of schemas."
        == str(exc_info.value)
    )


@pytest.mark.asyncio
async def test_add_field_dependencies_with_invalid_dependencies_arg_raises_error(
    httpx_mock, schema_json
):
    httpx_mock.add_response(url="http://graphql.example.com/", json=schema_json)

    proxy_schema = ProxySchema()
    schema_id = proxy_schema.add_remote_schema("http://graphql.example.com/")

    with pytest.raises(ValueError) as exc_info:
        proxy_schema.add_field_dependencies(
            schema_id, "Complex", "class", "group { id }"
        )

    assert (
        "'class' field dependencies should be defined as a single GraphQL "
        "operation, e.g.: '{ field other { subfield } }'."
    ) == str(exc_info.value)


@pytest.mark.asyncio
async def test_add_field_dependencies_with_invalid_dependencies_arg_op_raises_error(
    httpx_mock, schema_json
):
    httpx_mock.add_response(url="http://graphql.example.com/", json=schema_json)

    proxy_schema = ProxySchema()
    schema_id = proxy_schema.add_remote_schema("http://graphql.example.com/")

    with pytest.raises(ValueError) as exc_info:
        proxy_schema.add_field_dependencies(
            schema_id, "Complex", "class", "mutation { group { id } }"
        )

    assert (
        "'class' field dependencies should be defined as a single GraphQL "
        "operation, e.g.: '{ field other { subfield } }'."
    ) == str(exc_info.value)


@pytest.mark.asyncio
async def test_root_value_for_remote_schema_includes_field_dependencies(
    httpx_mock, schema_json
):
    httpx_mock.add_response(url="http://graphql.example.com/", json=schema_json)
    httpx_mock.add_response(url="http://graphql.example.com/", json={"data": {}})
    proxy_schema = ProxySchema()
    schema_id = proxy_schema.add_remote_schema("http://graphql.example.com/")

    proxy_schema.add_field_dependencies(
        schema_id, "Complex", "class", "{ group { id } }"
    )

    proxy_schema.get_final_schema()

    await proxy_schema.root_resolver(
        {},
        "TestQuery",
        {},
        parse(
            """
            query TestQuery {
              complex {
                class
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
              complex {
                group {
                  id
                }
                class
              }
            }
            """
        ).strip(),
    }


@pytest.mark.asyncio
async def test_alias_aware_resolver_is_added_to_fields():
    proxy_schema = ProxySchema()

    schema_def = """
        type Query {
            product: Product
        }

        type Product {
            id: ID!
            name: String!
            attributes: [Attribute!]
        }

        type Attribute {
            key: String!
            value: String!
        }
        """

    from graphql import build_schema

    schema = build_schema(schema_def)
    proxy_schema.add_schema(schema)

    final_schema = proxy_schema.get_final_schema()

    product_type = final_schema.type_map["Product"]
    assert isinstance(product_type, GraphQLObjectType)
    assert product_type.fields["attributes"].resolve is not None
    assert product_type.fields["name"].resolve is not None
    assert product_type.fields["id"].resolve is not None


@pytest.mark.asyncio
async def test_alias_aware_resolver_handles_aliased_field(httpx_mock, schema_json):
    httpx_mock.add_response(json=schema_json)
    httpx_mock.add_response(
        json={
            "data": {
                "complex": {
                    "id": "123",
                    "displayName": "Test Name",
                }
            }
        }
    )
    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/")
    proxy_schema.get_final_schema()
    root_value = await proxy_schema.root_resolver(
        {},
        "Query",
        None,
        parse("query Query { complex { id, displayName: name } }"),
    )

    assert root_value == {
        "complex": {
            "id": "123",
            "displayName": "Test Name",
        }
    }


@pytest.mark.asyncio
async def test_multiple_aliases_for_same_field(httpx_mock, schema_json):
    httpx_mock.add_response(json=schema_json)
    httpx_mock.add_response(
        json={
            "data": {
                "complex": {
                    "name1": "Test Name",
                    "name2": "Test Name",
                    "name3": "Test Name",
                }
            }
        }
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/")

    proxy_schema.get_final_schema()

    root_value = await proxy_schema.root_resolver(
        {},
        "Query",
        None,
        parse(
            """
            query Query {
                complex {
                    name1: name
                    name2: name
                    name3: name
                }
            }
            """
        ),
    )

    assert root_value == {
        "complex": {
            "name1": "Test Name",
            "name2": "Test Name",
            "name3": "Test Name",
        }
    }


@pytest.mark.asyncio
async def test_alias_with_arguments(httpx_mock, schema_json):
    httpx_mock.add_response(json=schema_json)
    httpx_mock.add_response(
        json={
            "data": {
                "complex": {
                    "name1": "Test Name",
                }
            }
        }
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/")

    proxy_schema.get_final_schema()

    root_value = await proxy_schema.root_resolver(
        {},
        "Query",
        None,
        parse(
            """
            query Query {
                complex {
                    name1: name(arg: test)
                }
            }
            """
        ),
    )

    assert root_value == {
        "complex": {
            "name1": "Test Name",
        }
    }


@pytest.mark.asyncio
async def test_nested_aliases(httpx_mock, schema_json):
    httpx_mock.add_response(json=schema_json)
    httpx_mock.add_response(
        json={
            "data": {
                "myComplex": {
                    "identifier": "123",
                    "displayName": "Test",
                    "myGroup": {"groupId": "456", "groupName": "Group Test"},
                }
            }
        }
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_remote_schema("http://graphql.example.com/")

    proxy_schema.get_final_schema()

    root_value = await proxy_schema.root_resolver(
        {},
        "Query",
        None,
        parse(
            """
            query Query {
                myComplex: complex {
                    identifier: id
                    displayName: name
                    myGroup: group {
                        groupId: id
                        groupName: name
                    }
                }
            }
            """
        ),
    )

    assert root_value == {
        "myComplex": {
            "identifier": "123",
            "displayName": "Test",
            "myGroup": {"groupId": "456", "groupName": "Group Test"},
        }
    }


@pytest.mark.asyncio
async def test_alias_aware_resolver_preserves_original_resolver():
    def original_resolver(obj, info):
        return "original_value"

    from graphql import build_schema

    schema = build_schema(
        """
        type Query {
            test: String
        }
        """
    )

    schema.type_map["Query"].fields["test"].resolve = original_resolver

    proxy_schema = ProxySchema()
    proxy_schema.add_schema(schema)

    final_schema = proxy_schema.get_final_schema()

    query_type = final_schema.type_map["Query"]
    new_resolver = query_type.fields["test"].resolve
    assert new_resolver is not None
    assert new_resolver != original_resolver

    info = Mock()
    info.field_nodes = []

    result = new_resolver({}, info)
    assert result == "original_value"


@pytest.mark.asyncio
async def test_alias_aware_resolver_handles_dict_and_object_sources():
    from graphql import build_schema

    schema = build_schema(
        """
        type Query {
            test: String
        }
        """
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_schema(schema)
    final_schema = proxy_schema.get_final_schema()

    resolver = final_schema.type_map["Query"].fields["test"].resolve

    info = Mock()
    info.field_nodes = [Mock()]
    info.field_nodes[0].alias = None

    dict_source = {"test": "dict_value"}
    assert resolver(dict_source, info) == "dict_value"

    class ObjSource:
        test = "obj_value"

    obj_source = ObjSource()
    assert resolver(obj_source, info) == "obj_value"

    info.field_nodes[0].alias = Mock()
    info.field_nodes[0].alias.value = "myAlias"
    dict_with_alias = {"myAlias": "alias_value", "test": "original_value"}
    assert resolver(dict_with_alias, info) == "alias_value"


@pytest.mark.asyncio
async def test_alias_aware_resolver_returns_none_when_field_not_found():
    from graphql import build_schema

    schema = build_schema(
        """
        type Query {
            test: String
        }
        """
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_schema(schema)
    final_schema = proxy_schema.get_final_schema()

    resolver = final_schema.type_map["Query"].fields["test"].resolve

    info = Mock()
    info.field_nodes = []

    assert resolver({}, info) is None

    class EmptyObj:
        pass

    assert resolver(EmptyObj(), info) is None


@pytest.mark.asyncio
async def test_get_final_schema_adds_resolvers_only_to_object_types():
    from graphql import build_schema

    schema = build_schema(
        """
        type Query {
            test: String
        }

        enum TestEnum {
            VALUE1
            VALUE2
        }

        input TestInput {
            field: String
        }

        interface TestInterface {
            id: ID!
        }
        """
    )

    proxy_schema = ProxySchema()
    proxy_schema.add_schema(schema)
    final_schema = proxy_schema.get_final_schema()

    for type_name, type_def in final_schema.type_map.items():
        if isinstance(type_def, GraphQLObjectType) and not type_name.startswith("__"):
            for field_name, field_def in type_def.fields.items():
                assert (
                    field_def.resolve is not None
                ), f"Missing resolver for {type_name}.{field_name}"
