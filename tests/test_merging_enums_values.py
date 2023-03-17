import pytest
from graphql import GraphQLEnumType, GraphQLEnumValue

from ariadne_graphql_proxy.merge import merge_enums_values


def test_merge_enums_values_returns_enums_values_from_both_enums():
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

    merged_values = merge_enums_values(enum1, enum2)

    assert isinstance(merged_values, dict)
    assert merged_values["VAL1"]
    assert merged_values["VAL2"]
    assert merged_values["VAL3"]


def test_merge_enums_values_raises_type_error_for_not_matching_values():
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
            "VAL1": GraphQLEnumValue(value="VAL_1"),
            "VAL3": GraphQLEnumValue(value="VAL3"),
        },
        extensions={"extension2": "2"},
    )

    with pytest.raises(TypeError):
        merge_enums_values(enum1, enum2)


def test_merge_enums_values_returns_value_with_description_from_first_value():
    enum1 = GraphQLEnumType(
        name="EnumType",
        values={
            "VAL1": GraphQLEnumValue(value="VAL1", description="Hello World"),
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

    merged_values = merge_enums_values(enum1, enum2)

    assert isinstance(merged_values["VAL1"], GraphQLEnumValue)
    assert merged_values["VAL1"].description == "Hello World"


def test_merge_enums_values_returns_value_with_description_from_other_value():
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
            "VAL1": GraphQLEnumValue(value="VAL1", description="Hello World"),
            "VAL3": GraphQLEnumValue(value="VAL3"),
        },
        extensions={"extension2": "2"},
    )

    merged_values = merge_enums_values(enum1, enum2)

    assert isinstance(merged_values["VAL1"], GraphQLEnumValue)
    assert merged_values["VAL1"].description == "Hello World"


def test_merge_enums_values_raises_type_error_for_not_matching_descriptions():
    enum1 = GraphQLEnumType(
        name="EnumType",
        values={
            "VAL1": GraphQLEnumValue(value="VAL1", description="Lorem ipsum"),
            "VAL2": GraphQLEnumValue(value="VAL2"),
        },
        extensions={"extension1": "1"},
    )
    enum2 = GraphQLEnumType(
        name="EnumType",
        values={
            "VAL1": GraphQLEnumValue(value="VAL1", description="Dolor met"),
            "VAL3": GraphQLEnumValue(value="VAL3"),
        },
        extensions={"extension2": "2"},
    )

    with pytest.raises(TypeError):
        merge_enums_values(enum1, enum2)


def test_merge_enums_values_returns_value_with_deprecation_reason_from_first_value():
    enum1 = GraphQLEnumType(
        name="EnumType",
        values={
            "VAL1": GraphQLEnumValue(value="VAL1", deprecation_reason="Hello World"),
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

    merged_values = merge_enums_values(enum1, enum2)

    assert isinstance(merged_values["VAL1"], GraphQLEnumValue)
    assert merged_values["VAL1"].deprecation_reason == "Hello World"


def test_merge_enums_values_returns_value_with_deprecation_reason_from_other_value():
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
            "VAL1": GraphQLEnumValue(value="VAL1", deprecation_reason="Hello World"),
            "VAL3": GraphQLEnumValue(value="VAL3"),
        },
        extensions={"extension2": "2"},
    )

    merged_values = merge_enums_values(enum1, enum2)

    assert isinstance(merged_values["VAL1"], GraphQLEnumValue)
    assert merged_values["VAL1"].deprecation_reason == "Hello World"


def test_merge_enums_values_raises_type_error_for_not_matching_deprecation_reasons():
    enum1 = GraphQLEnumType(
        name="EnumType",
        values={
            "VAL1": GraphQLEnumValue(value="VAL1", deprecation_reason="Lorem ipsum"),
            "VAL2": GraphQLEnumValue(value="VAL2"),
        },
        extensions={"extension1": "1"},
    )
    enum2 = GraphQLEnumType(
        name="EnumType",
        values={
            "VAL1": GraphQLEnumValue(value="VAL1", deprecation_reason="Dolor met"),
            "VAL3": GraphQLEnumValue(value="VAL3"),
        },
        extensions={"extension2": "2"},
    )

    with pytest.raises(TypeError):
        merge_enums_values(enum1, enum2)
