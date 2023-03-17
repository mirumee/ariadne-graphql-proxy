import pytest
from graphql import GraphQLEnumType, GraphQLEnumValue

from ariadne_graphql_proxy.merge import merge_enums


def test_merge_enums_returns_enum_with_values_from_both_enums():
    enum1 = GraphQLEnumType(
        name="EnumType",
        values={
            "VAL1": GraphQLEnumValue(value="VAL1"),
            "VAL2": GraphQLEnumValue(value="VAL2"),
        },
        extensions={"extension1": "1"},
    )
    enum2 = GraphQLEnumType(
        name="EnumType",
        values={
            "VAL1": GraphQLEnumValue(value="VAL1"),
            "VAL3": GraphQLEnumValue(value="VAL3"),
        },
        extensions={"extension2": "2"},
    )

    merged_enum = merge_enums(enum1, enum2)

    assert isinstance(merged_enum, GraphQLEnumType)
    assert merged_enum.values["VAL1"]
    assert merged_enum.values["VAL2"]
    assert merged_enum.values["VAL3"]
    assert merged_enum.extensions["extension1"]
    assert merged_enum.extensions["extension2"]


def test_merge_enums_returns_enum_with_description_from_first_enum():
    enum1 = GraphQLEnumType(
        name="EnumType",
        values={
            "VAL1": GraphQLEnumValue(value="VAL1"),
            "VAL2": GraphQLEnumValue(value="VAL2"),
        },
        description="Hello world!",
    )
    enum2 = GraphQLEnumType(
        name="EnumType",
        values={
            "VAL1": GraphQLEnumValue(value="VAL1"),
            "VAL3": GraphQLEnumValue(value="VAL3"),
        },
    )

    merged_enum = merge_enums(enum1, enum2)

    assert isinstance(merged_enum, GraphQLEnumType)
    assert merged_enum.description == "Hello world!"


def test_merge_enums_returns_enum_with_description_from_other_enum():
    enum1 = GraphQLEnumType(
        name="EnumType",
        values={
            "VAL1": GraphQLEnumValue(value="VAL1"),
            "VAL2": GraphQLEnumValue(value="VAL2"),
        },
    )
    enum2 = GraphQLEnumType(
        name="EnumType",
        values={
            "VAL1": GraphQLEnumValue(value="VAL1"),
            "VAL3": GraphQLEnumValue(value="VAL3"),
        },
        description="Hello world!",
    )

    merged_enum = merge_enums(enum1, enum2)

    assert isinstance(merged_enum, GraphQLEnumType)
    assert merged_enum.description == "Hello world!"


def test_merge_enums_raises_type_error_for_not_matching_descriptions():
    enum1 = GraphQLEnumType(
        name="EnumType",
        values={
            "VAL1": GraphQLEnumValue(value="VAL1"),
            "VAL2": GraphQLEnumValue(value="VAL2"),
        },
        description="Lorem ipsum",
    )
    enum2 = GraphQLEnumType(
        name="EnumType",
        values={
            "VAL1": GraphQLEnumValue(value="VAL1"),
            "VAL3": GraphQLEnumValue(value="VAL3"),
        },
        description="Dolor met",
    )

    with pytest.raises(TypeError):
        merge_enums(enum1, enum2)
