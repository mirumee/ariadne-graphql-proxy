from typing import Any, Optional

import pytest
from ariadne import make_executable_schema
from httpx import Headers, Response


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


@pytest.fixture
def gql():
    return lambda x: x


@pytest.fixture
def httpx_response():
    def create_response(
        json: Optional[Any] = None,
        text: Optional[Any] = None,
        status_code: int = 200,
    ) -> Response:
        if json and text:
            raise ValueError("'text' and 'json' arguments can't be combined")

        if json:
            return Response(
                status_code,
                headers=Headers(
                    {"content-type": "application/json; charset=utf-8"},
                    "utf-8",
                ),
                json=json,
            )

        if text:
            return Response(
                status_code,
                headers=Headers(
                    {"content-type": "text/plain; charset=utf-8"},
                    "utf-8",
                ),
                text=text,
            )

    return create_response
