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
    GraphQLString,
    GraphQLUnionType,
)

from ariadne_graphql_proxy.merge import merge_types


@pytest.mark.parametrize(
    "type1, type2, method_name",
    [
        (
            GraphQLEnumType(
                name="EnumType",
                values={
                    "VAL1": GraphQLEnumValue(value="VAL1"),
                    "VAL2": GraphQLEnumValue(value="VAL2"),
                },
            ),
            GraphQLEnumType(
                name="EnumType",
                values={
                    "VAL1": GraphQLEnumValue(value="VAL1"),
                    "VAL3": GraphQLEnumValue(value="VAL3"),
                },
            ),
            "merge_enums",
        ),
        (
            GraphQLObjectType(
                name="TypeA", fields={"valA": GraphQLField(type_=GraphQLString)}
            ),
            GraphQLObjectType(
                name="TypeA", fields={"valB": GraphQLField(type_=GraphQLString)}
            ),
            "merge_objects",
        ),
        (
            GraphQLInputObjectType(
                name="TypeA", fields={"valA": GraphQLInputField(type_=GraphQLString)}
            ),
            GraphQLInputObjectType(
                name="TypeA", fields={"valB": GraphQLInputField(type_=GraphQLString)}
            ),
            "merge_inputs",
        ),
        (
            GraphQLScalarType(name="ScalarName"),
            GraphQLScalarType(name="ScalarName"),
            "merge_scalars",
        ),
        (
            GraphQLInterfaceType(
                name="TypeA", fields={"valA": GraphQLField(type_=GraphQLString)}
            ),
            GraphQLInterfaceType(
                name="TypeA", fields={"valB": GraphQLField(type_=GraphQLString)}
            ),
            "merge_interfaces",
        ),
        (
            GraphQLUnionType(name="UnionType", types=()),
            GraphQLUnionType(name="UnionType", types=()),
            "merge_unions",
        ),
    ],
)
def test_merge_types_calls_correct_merge_method(mocker, type1, type2, method_name):
    mocked_merge_method = mocker.patch(f"ariadne_graphql_proxy.merge.{method_name}")

    merge_types(merged_types={}, type1=type1, type2=type2)

    assert mocked_merge_method.called
