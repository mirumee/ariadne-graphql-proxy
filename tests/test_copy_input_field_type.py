import pytest
from graphql import (
    GraphQLBoolean,
    GraphQLFloat,
    GraphQLID,
    GraphQLInt,
    GraphQLList,
    GraphQLNamedType,
    GraphQLNonNull,
    GraphQLString,
)

from ariadne_graphql_proxy import copy_input_field_type


@pytest.mark.parametrize(
    "field_type, expected",
    [
        (GraphQLBoolean, GraphQLBoolean),
        (GraphQLString, GraphQLString),
        (GraphQLFloat, GraphQLFloat),
        (GraphQLID, GraphQLID),
        (GraphQLInt, GraphQLInt),
    ],
)
def test_copy_input_field_type_returns_correct_scalar_type(field_type, expected):
    assert copy_input_field_type({}, field_type) == expected


def test_copy_input_field_type_returns_correct_named_type():
    field_type = GraphQLNamedType("NamedType")
    duplicated_type = GraphQLNamedType("NamedType")
    assert (
        copy_input_field_type({field_type.name: duplicated_type}, field_type)
        == duplicated_type
    )


@pytest.mark.parametrize(
    "field_type, expected",
    [
        (GraphQLList(GraphQLBoolean), GraphQLList),
        (GraphQLNonNull(GraphQLBoolean), GraphQLNonNull),
    ],
)
def test_copy_input_field_type_returns_correct_parent_type(field_type, expected):
    assert isinstance(copy_input_field_type({}, field_type), expected)
