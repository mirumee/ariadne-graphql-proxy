import pytest
from graphql import GraphQLFloat, GraphQLInputField, GraphQLString

from ariadne_graphql_proxy import merge_input_fields


def test_merge_input_fields_returns_field():
    field1 = GraphQLInputField(
        type_=GraphQLFloat,
        default_value=2.5,
        description="desc",
        deprecation_reason="reason",
        out_name="out name",
    )
    field2 = GraphQLInputField(
        type_=GraphQLFloat,
        default_value=2.5,
        description="desc",
        deprecation_reason="reason",
        out_name="out name",
    )

    merged_field = merge_input_fields(
        merged_types={},
        type_name="TestInput",
        field_name="testField",
        field1=field1,
        field2=field2,
    )

    assert isinstance(merged_field, GraphQLInputField)
    assert merged_field is not field1
    assert merged_field is not field2
    assert merged_field.default_value == field1.default_value
    assert merged_field.description == field1.description
    assert merged_field.deprecation_reason == field1.deprecation_reason
    assert merged_field.out_name == field1.out_name


def test_merge_input_fields_raises_type_error_for_not_matching_types():
    field1 = GraphQLInputField(type_=GraphQLString)
    field2 = GraphQLInputField(type_=GraphQLFloat)

    with pytest.raises(TypeError):
        merge_input_fields(
            merged_types={},
            type_name="TestInput",
            field_name="testField",
            field1=field1,
            field2=field2,
        )


def test_merge_input_fields_returns_field_with_default_value_from_first_field():
    field1 = GraphQLInputField(
        default_value="Hello world!",
        type_=GraphQLString,
    )
    field2 = GraphQLInputField(
        type_=GraphQLString,
    )

    merged_field = merge_input_fields(
        merged_types={},
        type_name="TestType",
        field_name="testField",
        field1=field1,
        field2=field2,
    )

    assert isinstance(merged_field, GraphQLInputField)
    assert merged_field.default_value == "Hello world!"


def test_merge_input_fields_returns_field_with_default_value_from_other_field():
    field1 = GraphQLInputField(
        type_=GraphQLString,
    )
    field2 = GraphQLInputField(
        default_value="Hello world!",
        type_=GraphQLString,
    )

    merged_field = merge_input_fields(
        merged_types={},
        type_name="TestType",
        field_name="testField",
        field1=field1,
        field2=field2,
    )

    assert isinstance(merged_field, GraphQLInputField)
    assert merged_field.default_value == "Hello world!"


def test_merge_input_fields_raises_type_error_for_not_matching_default_values():
    field1 = GraphQLInputField(
        default_value="Lorem ipsum",
        type_=GraphQLString,
    )
    field2 = GraphQLInputField(
        default_value="Dolor met",
        type_=GraphQLString,
    )

    with pytest.raises(TypeError):
        merge_input_fields(
            merged_types={},
            type_name="TestType",
            field_name="testField",
            field1=field1,
            field2=field2,
        )


def test_merge_input_fields_returns_field_with_out_name_from_first_field():
    field1 = GraphQLInputField(
        out_name="Hello world!",
        type_=GraphQLString,
    )
    field2 = GraphQLInputField(
        type_=GraphQLString,
    )

    merged_field = merge_input_fields(
        merged_types={},
        type_name="TestType",
        field_name="testField",
        field1=field1,
        field2=field2,
    )

    assert isinstance(merged_field, GraphQLInputField)
    assert merged_field.out_name == "Hello world!"


def test_merge_input_fields_returns_field_with_out_name_from_other_field():
    field1 = GraphQLInputField(
        type_=GraphQLString,
    )
    field2 = GraphQLInputField(
        out_name="Hello world!",
        type_=GraphQLString,
    )

    merged_field = merge_input_fields(
        merged_types={},
        type_name="TestType",
        field_name="testField",
        field1=field1,
        field2=field2,
    )

    assert isinstance(merged_field, GraphQLInputField)
    assert merged_field.out_name == "Hello world!"


def test_merge_input_fields_raises_type_error_for_not_matching_out_names():
    field1 = GraphQLInputField(
        out_name="Lorem ipsum",
        type_=GraphQLString,
    )
    field2 = GraphQLInputField(
        out_name="Dolor met",
        type_=GraphQLString,
    )

    with pytest.raises(TypeError):
        merge_input_fields(
            merged_types={},
            type_name="TestType",
            field_name="testField",
            field1=field1,
            field2=field2,
        )


def test_merge_input_fields_returns_field_with_description_from_first_field():
    field1 = GraphQLInputField(
        description="Hello world!",
        type_=GraphQLString,
    )
    field2 = GraphQLInputField(
        type_=GraphQLString,
    )

    merged_field = merge_input_fields(
        merged_types={},
        type_name="TestType",
        field_name="testField",
        field1=field1,
        field2=field2,
    )

    assert isinstance(merged_field, GraphQLInputField)
    assert merged_field.description == "Hello world!"


def test_merge_input_fields_returns_field_with_description_from_other_field():
    field1 = GraphQLInputField(
        type_=GraphQLString,
    )
    field2 = GraphQLInputField(
        description="Hello world!",
        type_=GraphQLString,
    )

    merged_field = merge_input_fields(
        merged_types={},
        type_name="TestType",
        field_name="testField",
        field1=field1,
        field2=field2,
    )

    assert isinstance(merged_field, GraphQLInputField)
    assert merged_field.description == "Hello world!"


def test_merge_input_fields_raises_type_error_for_not_matching_descriptions():
    field1 = GraphQLInputField(
        description="Lorem ipsum",
        type_=GraphQLString,
    )
    field2 = GraphQLInputField(
        description="Dolor met",
        type_=GraphQLString,
    )

    with pytest.raises(TypeError):
        merge_input_fields(
            merged_types={},
            type_name="TestType",
            field_name="testField",
            field1=field1,
            field2=field2,
        )


def test_merge_input_fields_returns_field_with_deprecation_reason_from_both_fields():
    field1 = GraphQLInputField(
        deprecation_reason="Hello world!",
        type_=GraphQLString,
    )
    field2 = GraphQLInputField(
        deprecation_reason="Hello world!",
        type_=GraphQLString,
    )

    merged_field = merge_input_fields(
        merged_types={},
        type_name="TestType",
        field_name="testField",
        field1=field1,
        field2=field2,
    )

    assert isinstance(merged_field, GraphQLInputField)
    assert merged_field.deprecation_reason == "Hello world!"


def test_merge_input_fields_returns_field_with_deprecation_reason_from_first_field():
    field1 = GraphQLInputField(
        deprecation_reason="Hello world!",
        type_=GraphQLString,
    )
    field2 = GraphQLInputField(
        type_=GraphQLString,
    )

    merged_field = merge_input_fields(
        merged_types={},
        type_name="TestType",
        field_name="testField",
        field1=field1,
        field2=field2,
    )

    assert isinstance(merged_field, GraphQLInputField)
    assert merged_field.deprecation_reason == "Hello world!"


def test_merge_input_fields_returns_field_with_deprecation_reason_from_other_field():
    field1 = GraphQLInputField(
        type_=GraphQLString,
    )
    field2 = GraphQLInputField(
        deprecation_reason="Hello world!",
        type_=GraphQLString,
    )

    merged_field = merge_input_fields(
        merged_types={},
        type_name="TestType",
        field_name="testField",
        field1=field1,
        field2=field2,
    )

    assert isinstance(merged_field, GraphQLInputField)
    assert merged_field.deprecation_reason == "Hello world!"


def test_merge_input_fields_raises_type_error_for_not_matching_deprecation_reasons():
    field1 = GraphQLInputField(
        deprecation_reason="Lorem ipsum",
        type_=GraphQLString,
    )
    field2 = GraphQLInputField(
        deprecation_reason="Dolor met",
        type_=GraphQLString,
    )

    with pytest.raises(TypeError):
        merge_input_fields(
            merged_types={},
            type_name="TestType",
            field_name="testField",
            field1=field1,
            field2=field2,
        )
