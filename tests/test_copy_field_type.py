import pytest
from graphql import (
    GraphQLBoolean,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLFloat,
    GraphQLID,
    GraphQLInt,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLString,
)

from ariadne_graphql_proxy import copy_field_type


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
def test_copy_field_type_returns_correct_scalar_type(field_type, expected):
    assert copy_field_type({}, field_type) == expected


@pytest.mark.parametrize(
    "field_type, duplicated_type",
    [
        (
            GraphQLObjectType(
                name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
            ),
            GraphQLObjectType(
                name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
            ),
        ),
        (
            GraphQLEnumType(
                name="EnumType",
                values={
                    "VAL1": GraphQLEnumValue(value="VAL1"),
                },
            ),
            GraphQLEnumType(
                name="EnumType",
                values={
                    "VAL1": GraphQLEnumValue(value="VAL1"),
                },
            ),
        ),
        (
            GraphQLInterfaceType(
                name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
            ),
            GraphQLInterfaceType(
                name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
            ),
        ),
    ],
)
def test_copy_field_type_returns_correct_related_type(field_type, duplicated_type):
    assert (
        copy_field_type({field_type.name: duplicated_type}, field_type)
        == duplicated_type
    )


@pytest.mark.parametrize(
    "field_type, expected",
    [
        (GraphQLList(GraphQLBoolean), GraphQLList),
        (GraphQLNonNull(GraphQLBoolean), GraphQLNonNull),
    ],
)
def test_copy_field_type_returns_correct_parent_type(field_type, expected):
    assert isinstance(copy_field_type({}, field_type), expected)
