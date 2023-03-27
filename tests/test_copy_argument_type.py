import pytest
from graphql import (
    GraphQLBoolean,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLFloat,
    GraphQLID,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInt,
    GraphQLList,
    GraphQLNonNull,
    GraphQLString,
)

from ariadne_graphql_proxy import copy_argument_type


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
def test_copy_argument_type_returns_correct_scalar_type(field_type, expected):
    assert copy_argument_type({}, field_type) == expected


@pytest.mark.parametrize(
    "field_type, duplicated_type",
    [
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
            GraphQLInputObjectType(
                name="InputType", fields={"field1": GraphQLInputField(GraphQLBoolean)}
            ),
            GraphQLInputObjectType(
                name="InputType", fields={"field1": GraphQLInputField(GraphQLBoolean)}
            ),
        ),
    ],
)
def test_copy_argument_type_returns_correct_related_type(field_type, duplicated_type):
    assert (
        copy_argument_type({field_type.name: duplicated_type}, field_type)
        == duplicated_type
    )


@pytest.mark.parametrize(
    "field_type, expected",
    [
        (GraphQLList(GraphQLBoolean), GraphQLList),
        (GraphQLNonNull(GraphQLBoolean), GraphQLNonNull),
    ],
)
def test_copy_argument_type_returns_correct_parent_type(field_type, expected):
    assert isinstance(copy_argument_type({}, field_type), expected)
