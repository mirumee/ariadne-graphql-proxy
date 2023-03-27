import pytest
from graphql import (
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLString,
    GraphQLUnionType,
)

from ariadne_graphql_proxy import copy_schema_types


@pytest.mark.parametrize(
    "graphql_type, expected_method_name",
    [
        (
            GraphQLEnumType(
                name="EnumType",
                values={
                    "VAL1": GraphQLEnumValue(value="VAL1"),
                    "VAL2": GraphQLEnumValue(value="VAL2"),
                },
            ),
            "copy_enum",
        ),
        (
            GraphQLObjectType(
                name="TypeA", fields={"val": GraphQLField(type_=GraphQLString)}
            ),
            "copy_object",
        ),
        (
            GraphQLInputObjectType(
                name="TypeA", fields={"val": GraphQLInputField(type_=GraphQLString)}
            ),
            "copy_input",
        ),
        (
            GraphQLScalarType(name="ScalarName"),
            "copy_scalar",
        ),
        (
            GraphQLInterfaceType(
                name="TypeA", fields={"val": GraphQLField(type_=GraphQLString)}
            ),
            "copy_interface",
        ),
        (
            GraphQLUnionType(name="UnionType", types=()),
            "copy_union",
        ),
    ],
)
def test_copy_schema_types_calls_correct_copy_method_for_type(
    mocker, graphql_type, expected_method_name
):
    mocked_copy_method = mocker.patch(
        f"ariadne_graphql_proxy.copy.{expected_method_name}"
    )

    copy_schema_types(GraphQLSchema(types=[graphql_type]))

    assert mocked_copy_method.called
