import json
from textwrap import dedent

import pytest
from ariadne.graphql import graphql

from ariadne_graphql_proxy import ForeignKeyResolver, ProxySchema, set_resolver

GRAPHQL_URL = "http://upstream.example.com/graphql/"


@pytest.mark.asyncio
async def test_foreign_key_resolver_fetches_related_object(
    httpx_mock,
    store_schema_json,
    order_create_schema_json,
    store_root_value,
):
    # Store GraphQL introspection
    httpx_mock.add_response(
        url="http://graphql.example.com/store/", json=store_schema_json
    )

    # Store Order result for FKey
    httpx_mock.add_response(
        url="http://graphql.example.com/store/",
        json={
            "data": {"order": store_root_value["order"]},
        },
    )

    # Order create service introspection
    httpx_mock.add_response(
        url="http://graphql.example.com/order/", json=order_create_schema_json
    )

    # Order create service mutation
    httpx_mock.add_response(
        url="http://graphql.example.com/order/",
        json={
            "data": {
                "orderCreate": {
                    "order": {
                        "id": store_root_value["order"]["id"],
                    },
                    "errors": None,
                }
            }
        },
    )

    proxy_schema = ProxySchema()

    proxy_schema.add_remote_schema(
        "http://graphql.example.com/store/",
        exclude_fields={"Mutation": ["orderCreate"]},
    )
    proxy_schema.add_remote_schema("http://graphql.example.com/order/")

    proxy_schema.add_foreign_key("OrderCreate", "order", "id")

    final_schema = proxy_schema.get_final_schema()

    foreign_key_resolver = ForeignKeyResolver(
        "http://graphql.example.com/store/",
        """
        query GetOrder($id: ID!) {
            order(id: $id) {
                __FIELDS
            }
        }
        """,
        {"id": "id"},
    )

    set_resolver(final_schema, "OrderCreate", "order", foreign_key_resolver)

    success, data = await graphql(
        final_schema,
        {
            "operationName": "OrderCreate",
            "query": (
                """
                mutation OrderCreate {
                    orderCreate(customer: "John", address: "Dolor", country: "Ipsum") {
                        order { id customer address country }
                        errors
                    }
                }
                """
            ),
            "variables": None,
        },
        context_value={"headers": {}},
        root_value=proxy_schema.root_resolver,
    )

    assert success
    assert not data.get("errors")
    assert data == {
        "data": {
            "orderCreate": {
                "errors": None,
                "order": {
                    "address": "LongStrasse",
                    "country": "Midgar",
                    "customer": "John Doe",
                    "id": "5s87d6sa85f7asds",
                },
            },
        },
    }

    mutation_request = httpx_mock.get_requests(url="http://graphql.example.com/order/")[
        -1
    ]
    assert json.loads(mutation_request.content) == {
        "operationName": "OrderCreate",
        "variables": None,
        "query": dedent(
            """
            mutation OrderCreate {
              orderCreate(customer: "John", address: "Dolor", country: "Ipsum") {
                order {
                  id
                }
                errors
              }
            }
            """
        ).strip(),
    }

    order_fk_request = httpx_mock.get_requests(url="http://graphql.example.com/store/")[
        -1
    ]
    assert json.loads(order_fk_request.content) == {
        "operationName": "GetOrder",
        "variables": {"id": store_root_value["order"]["id"]},
        "query": dedent(
            """
            query GetOrder($id: ID!) {
              order(id: $id) {
                id
                customer
                address
                country
              }
            }
            """
        ).strip(),
    }


@pytest.mark.asyncio
async def test_foreign_key_resolver_fetches_related_object_with_implicit_variables(
    httpx_mock,
    store_schema_json,
    order_create_schema_json,
    store_root_value,
):
    # Store GraphQL introspection
    httpx_mock.add_response(
        url="http://graphql.example.com/store/", json=store_schema_json
    )

    # Store Order result for FKey
    httpx_mock.add_response(
        url="http://graphql.example.com/store/",
        json={
            "data": {"order": store_root_value["order"]},
        },
    )

    # Order create service introspection
    httpx_mock.add_response(
        url="http://graphql.example.com/order/", json=order_create_schema_json
    )

    # Order create service mutation
    httpx_mock.add_response(
        url="http://graphql.example.com/order/",
        json={
            "data": {
                "orderCreate": {
                    "order": {
                        "id": store_root_value["order"]["id"],
                    },
                    "errors": None,
                }
            }
        },
    )

    proxy_schema = ProxySchema()

    proxy_schema.add_remote_schema(
        "http://graphql.example.com/store/",
        exclude_fields={"Mutation": ["orderCreate"]},
    )
    proxy_schema.add_remote_schema("http://graphql.example.com/order/")

    proxy_schema.add_foreign_key("OrderCreate", "order", "id")

    final_schema = proxy_schema.get_final_schema()

    foreign_key_resolver = ForeignKeyResolver(
        "http://graphql.example.com/store/",
        """
        query GetOrder($id: ID!) {
            order(id: $id) {
                __FIELDS
            }
        }
        """,
    )

    set_resolver(final_schema, "OrderCreate", "order", foreign_key_resolver)

    success, data = await graphql(
        final_schema,
        {
            "operationName": "OrderCreate",
            "query": (
                """
                mutation OrderCreate {
                    orderCreate(customer: "John", address: "Dolor", country: "Ipsum") {
                        order { id customer address country }
                        errors
                    }
                }
                """
            ),
            "variables": None,
        },
        context_value={"headers": {}},
        root_value=proxy_schema.root_resolver,
    )

    assert success
    assert not data.get("errors")
    assert data == {
        "data": {
            "orderCreate": {
                "errors": None,
                "order": {
                    "address": "LongStrasse",
                    "country": "Midgar",
                    "customer": "John Doe",
                    "id": "5s87d6sa85f7asds",
                },
            },
        },
    }

    mutation_request = httpx_mock.get_requests(url="http://graphql.example.com/order/")[
        -1
    ]
    assert json.loads(mutation_request.content) == {
        "operationName": "OrderCreate",
        "variables": None,
        "query": dedent(
            """
            mutation OrderCreate {
              orderCreate(customer: "John", address: "Dolor", country: "Ipsum") {
                order {
                  id
                }
                errors
              }
            }
            """
        ).strip(),
    }

    order_fk_request = httpx_mock.get_requests(url="http://graphql.example.com/store/")[
        -1
    ]
    assert json.loads(order_fk_request.content) == {
        "operationName": "GetOrder",
        "variables": {"id": store_root_value["order"]["id"]},
        "query": dedent(
            """
            query GetOrder($id: ID!) {
              order(id: $id) {
                id
                customer
                address
                country
              }
            }
            """
        ).strip(),
    }


def test_foreign_key_resolver_raises_error_if_template_defines_multiple_operations():
    with pytest.raises(ValueError) as excinfo:
        ForeignKeyResolver(
            "http://graphql.example.com/store/",
            """
            query GetOrder($id: ID!) {
                order(id: $id) {
                    id
                }
            }

            query GetOther($id: ID!) {
                order(id: $id) {
                    id
                }
            }
            """,
        )

    assert "Query template must define single operation." in str(excinfo.value)


def test_foreign_key_resolver_raises_error_if_template_defines_anonymous_operation():
    with pytest.raises(ValueError) as excinfo:
        ForeignKeyResolver(
            "http://graphql.example.com/store/",
            """
            query {
                order(id: $id) {
                    id
                }
            }
            """,
        )

    assert "Query template operation must be named." in str(excinfo.value)


def test_foreign_key_resolver_raises_error_if_template_defines_fragment():
    with pytest.raises(ValueError) as excinfo:
        ForeignKeyResolver(
            "http://graphql.example.com/store/",
            """
            fragment Data on Query {
                order(id: $id) {
                    id
                }
            }
            """,
        )

    assert "Query template must define single operation." in str(excinfo.value)


def test_foreign_key_resolver_raises_error_if_template_is_missing_placeholder():
    with pytest.raises(ValueError) as excinfo:
        ForeignKeyResolver(
            "http://graphql.example.com/store/",
            """
            query GetOrder($id: ID!) {
                order(id: $id) {
                    id
                }
            }
            """,
        )

    assert "Query template operation should specify one" in str(excinfo.value)
    assert "It specifies 0." in str(excinfo.value)


def test_foreign_key_resolver_raises_error_if_template_has_multiple_placeholders():
    with pytest.raises(ValueError) as excinfo:
        ForeignKeyResolver(
            "http://graphql.example.com/store/",
            """
            query GetOrder($id: ID!) {
                order(id: $id) {
                    __FIELDS
                }
                __FIELDS
            }
            """,
        )

    assert "Query template operation should specify one" in str(excinfo.value)
    assert "It specifies 2." in str(excinfo.value)
