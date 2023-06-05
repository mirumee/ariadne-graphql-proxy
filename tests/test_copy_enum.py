from graphql import GraphQLEnumType, GraphQLEnumValue

from ariadne_graphql_proxy import copy_enum


def test_copy_enum_returns_new_enum_with_the_same_values():
    graphql_type = GraphQLEnumType(
        name="EnumType",
        values={
            "VAL1": GraphQLEnumValue(value="VAL1"),
            "VAL2": GraphQLEnumValue(value="VAL2"),
        },
        description="description",
        extensions={},
    )

    copied_type = copy_enum(graphql_type)

    assert isinstance(copied_type, GraphQLEnumType)
    assert copied_type is not graphql_type
    assert copied_type.name == graphql_type.name
    assert copied_type.values == graphql_type.values
    assert copied_type.description == graphql_type.description
    assert copied_type.extensions == graphql_type.extensions


def test_copy_enum_returns_new_enum_without_excluded_fields():
    graphql_type = GraphQLEnumType(
        name="EnumType",
        values={
            "VAL1": GraphQLEnumValue(value="VAL1"),
            "VAL2": GraphQLEnumValue(value="VAL2"),
            "VAL3": GraphQLEnumValue(value="VAL3"),
        },
    )

    copied_type = copy_enum(graphql_type, object_exclude_fields=["VAL1"])

    assert isinstance(copied_type, GraphQLEnumType)
    assert copied_type is not graphql_type
    assert "VAL1" not in copied_type.values
