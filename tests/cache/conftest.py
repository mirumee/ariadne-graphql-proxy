import pytest
from ariadne import make_executable_schema


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
    }
