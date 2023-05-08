from typing import Any, Optional

import pytest
from ariadne import make_executable_schema
from graphql import get_introspection_query, graphql_sync


@pytest.fixture
def schema():
    return make_executable_schema(
        """
        scalar Generic

        type Query {
            basic(arg: Generic, other: Generic): String
            complex(arg: Generic, other: Generic): Complex
        }

        type Complex {
            id: ID!
            name(arg: Generic, other: Generic): String!
            class(arg: Generic, other: Generic): String!
            group(arg: Generic, other: Generic): Group!
        }

        type Group {
            id(arg: Generic, other: Generic): ID!
            name(arg: Generic, other: Generic): String!
            rank(arg: Generic, other: Generic): Int!
        }
        """
    )


@pytest.fixture
def schema_json(schema):
    schema_data = graphql_sync(schema, get_introspection_query()).data
    return {"data": schema_data}


@pytest.fixture
def other_schema():
    return make_executable_schema(
        """
        scalar Generic

        type Query {
            other(arg: Generic, other: Generic): String
            otherComplex(arg: Generic, other: Generic): OtherComplex
        }

        type OtherComplex {
            id: ID!
            name(arg: Generic, other: Generic): String!
            class(arg: Generic, other: Generic): String!
            group(arg: Generic, other: Generic): OtherGroup!
        }

        type OtherGroup {
            id(arg: Generic, other: Generic): ID!
            name(arg: Generic, other: Generic): String!
            rank(arg: Generic, other: Generic): Int!
        }
        """
    )


@pytest.fixture
def other_schema_json(other_schema):
    schema_data = graphql_sync(other_schema, get_introspection_query()).data
    return {"data": schema_data}


@pytest.fixture
def complex_schema():
    return make_executable_schema(
        """
        scalar Generic

        type Query {
            complex(arg: Generic, other: Generic): Complex
        }

        type Complex {
            id: ID!
        }
        """
    )


@pytest.fixture
def complex_schema_json(complex_schema):
    schema_data = graphql_sync(complex_schema, get_introspection_query()).data
    return {"data": schema_data}


@pytest.fixture
def root_value():
    return {
        "basic": "Lorem Ipsum",
        "complex": {
            "id": 123,
            "name": "Test Type",
            "class": "demo",
            "group": {
                "id": 321,
                "name": "Testing",
                "rank": 9001,
            },
        },
        "other": "Dolor Met",
        "otherComplex": {
            "id": 123,
            "name": "Test Type",
            "class": "demo",
            "group": {
                "id": 321,
                "name": "Testing",
                "rank": 9001,
            },
        },
    }


@pytest.fixture
def gql():
    return lambda x: x
