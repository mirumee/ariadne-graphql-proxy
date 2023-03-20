import pytest
from graphql import (
    GraphQLArgument,
    GraphQLField,
    GraphQLFloat,
    GraphQLInt,
    GraphQLList,
    GraphQLNonNull,
    GraphQLString,
)

from ariadne_graphql_proxy.merge import merge_fields


def test_merge_fields_returns_field_with_arguments_from_both_fields():
    field1 = GraphQLField(
        type_=GraphQLString,
        args={
            "arg1": GraphQLArgument(type_=GraphQLString),
            "arg2": GraphQLArgument(type_=GraphQLString),
        },
    )
    field2 = GraphQLField(
        type_=GraphQLString,
        args={
            "arg1": GraphQLArgument(type_=GraphQLString),
            "arg3": GraphQLArgument(type_=GraphQLString),
        },
    )

    merged_field = merge_fields(
        merged_types={},
        type_name="TestType",
        field_name="testField",
        field1=field1,
        field2=field2,
    )

    assert isinstance(merged_field, GraphQLField)
    assert merged_field.args["arg1"]
    assert merged_field.args["arg2"]
    assert merged_field.args["arg3"]


def test_merge_fields_returns_field_with_copied_arguments_from_one_field():
    field1 = GraphQLField(
        type_=GraphQLString,
        args={
            "arg1": GraphQLArgument(type_=GraphQLString),
            "arg2": GraphQLArgument(type_=GraphQLString),
        },
    )
    field2 = GraphQLField(type_=GraphQLString)

    merged_field = merge_fields(
        merged_types={},
        type_name="TestType",
        field_name="testField",
        field1=field1,
        field2=field2,
    )

    assert isinstance(merged_field, GraphQLField)
    assert merged_field.args["arg1"]
    assert merged_field.args["arg1"] is not field1.args["arg1"]
    assert merged_field.args["arg2"]
    assert merged_field.args["arg2"] is not field1.args["arg2"]


def test_merge_fields_returns_field_with_description_from_both_fields():
    field1 = GraphQLField(
        description="Hello world!",
        type_=GraphQLString,
    )
    field2 = GraphQLField(
        description="Hello world!",
        type_=GraphQLString,
    )

    merged_field = merge_fields(
        merged_types={},
        type_name="TestType",
        field_name="testField",
        field1=field1,
        field2=field2,
    )

    assert isinstance(merged_field, GraphQLField)
    assert merged_field.description == "Hello world!"


def test_merge_fields_returns_field_with_description_from_first_field():
    field1 = GraphQLField(
        description="Hello world!",
        type_=GraphQLString,
    )
    field2 = GraphQLField(
        type_=GraphQLString,
    )

    merged_field = merge_fields(
        merged_types={},
        type_name="TestType",
        field_name="testField",
        field1=field1,
        field2=field2,
    )

    assert isinstance(merged_field, GraphQLField)
    assert merged_field.description == "Hello world!"


def test_merge_fields_returns_field_with_description_from_other_field():
    field1 = GraphQLField(
        type_=GraphQLString,
    )
    field2 = GraphQLField(
        description="Hello world!",
        type_=GraphQLString,
    )

    merged_field = merge_fields(
        merged_types={},
        type_name="TestType",
        field_name="testField",
        field1=field1,
        field2=field2,
    )

    assert isinstance(merged_field, GraphQLField)
    assert merged_field.description == "Hello world!"


def test_merge_fields_raises_type_error_for_not_matching_descriptions():
    field1 = GraphQLField(
        description="Lorem ipsum",
        type_=GraphQLString,
    )
    field2 = GraphQLField(
        description="Dolor met",
        type_=GraphQLString,
    )

    with pytest.raises(TypeError):
        merge_fields(
            merged_types={},
            type_name="TestType",
            field_name="testField",
            field1=field1,
            field2=field2,
        )


def test_merge_fields_returns_field_with_deprecation_reason_from_both_fields():
    field1 = GraphQLField(
        deprecation_reason="Hello world!",
        type_=GraphQLString,
    )
    field2 = GraphQLField(
        deprecation_reason="Hello world!",
        type_=GraphQLString,
    )

    merged_field = merge_fields(
        merged_types={},
        type_name="TestType",
        field_name="testField",
        field1=field1,
        field2=field2,
    )

    assert isinstance(merged_field, GraphQLField)
    assert merged_field.deprecation_reason == "Hello world!"


def test_merge_fields_returns_field_with_deprecation_reason_from_first_field():
    field1 = GraphQLField(
        deprecation_reason="Hello world!",
        type_=GraphQLString,
    )
    field2 = GraphQLField(
        type_=GraphQLString,
    )

    merged_field = merge_fields(
        merged_types={},
        type_name="TestType",
        field_name="testField",
        field1=field1,
        field2=field2,
    )

    assert isinstance(merged_field, GraphQLField)
    assert merged_field.deprecation_reason == "Hello world!"


def test_merge_fields_returns_field_with_deprecation_reason_from_other_field():
    field1 = GraphQLField(
        type_=GraphQLString,
    )
    field2 = GraphQLField(
        deprecation_reason="Hello world!",
        type_=GraphQLString,
    )

    merged_field = merge_fields(
        merged_types={},
        type_name="TestType",
        field_name="testField",
        field1=field1,
        field2=field2,
    )

    assert isinstance(merged_field, GraphQLField)
    assert merged_field.deprecation_reason == "Hello world!"


def test_merge_fields_raises_type_error_for_not_matching_deprecation_reasons():
    field1 = GraphQLField(
        deprecation_reason="Lorem ipsum",
        type_=GraphQLString,
    )
    field2 = GraphQLField(
        deprecation_reason="Dolor met",
        type_=GraphQLString,
    )

    with pytest.raises(TypeError):
        merge_fields(
            merged_types={},
            type_name="TestType",
            field_name="testField",
            field1=field1,
            field2=field2,
        )


@pytest.mark.parametrize(
    "type1, type2",
    [
        (GraphQLString, GraphQLFloat),
        (GraphQLString, GraphQLList(GraphQLString)),
        (GraphQLInt, GraphQLNonNull(GraphQLInt)),
    ],
)
def test_merge_fields_raises_type_error_for_not_matching_types(type1, type2):
    field1 = GraphQLField(type_=type1)
    field2 = GraphQLField(type_=type2)

    with pytest.raises(TypeError):
        merge_fields(
            merged_types={},
            type_name="TestType",
            field_name="testField",
            field1=field1,
            field2=field2,
        )
