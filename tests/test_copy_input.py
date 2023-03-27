from graphql import (
    GraphQLBoolean,
    GraphQLFloat,
    GraphQLInputField,
    GraphQLInputObjectType,
)

from ariadne_graphql_proxy import copy_input


def test_copy_input():
    related_field_type = GraphQLInputObjectType(
        "InputRelatedType",
        fields={
            "fieldA": GraphQLInputField(
                type_=GraphQLFloat,
            )
        },
    )
    duplicated_related_field_type = GraphQLInputObjectType(
        "InputRelatedType",
        fields={
            "fieldA": GraphQLInputField(
                type_=GraphQLFloat,
            )
        },
    )
    input_type = GraphQLInputObjectType(
        name="InputType",
        fields={
            "field1": GraphQLInputField(
                type_=GraphQLFloat,
                default_value=2.0,
                description="field1 description",
                deprecation_reason="reason",
                out_name="out name",
            ),
            "field2": GraphQLInputField(type_=related_field_type),
        },
    )

    copied_input_type = copy_input(
        {"InputRelatedType": duplicated_related_field_type}, input_type
    )

    assert isinstance(copied_input_type, GraphQLInputObjectType)
    assert copied_input_type is not input_type
    assert copied_input_type.name == input_type.name
    assert isinstance(copied_input_type.fields["field1"], GraphQLInputField)
    assert copied_input_type.fields["field1"] is not input_type.fields["field1"]
    assert copied_input_type.fields["field1"].type == GraphQLFloat
    assert (
        copied_input_type.fields["field1"].default_value
        == input_type.fields["field1"].default_value
    )
    assert (
        copied_input_type.fields["field1"].description
        == input_type.fields["field1"].description
    )
    assert (
        copied_input_type.fields["field1"].deprecation_reason
        == input_type.fields["field1"].deprecation_reason
    )
    assert (
        copied_input_type.fields["field1"].out_name
        == input_type.fields["field1"].out_name
    )
    assert isinstance(copied_input_type.fields["field2"], GraphQLInputField)
    assert copied_input_type.fields["field2"] is not input_type.fields["field2"]
    assert copied_input_type.fields["field2"].type == duplicated_related_field_type


def test_copy_input_returns_input_without_excluded_fields():
    input_type = GraphQLInputObjectType(
        name="InputType",
        fields={
            "field1": GraphQLInputField(type_=GraphQLFloat),
            "field2": GraphQLInputField(type_=GraphQLBoolean),
        },
    )

    copied_input_type = copy_input({}, input_type, object_exclude_fields=["field2"])

    assert isinstance(copied_input_type, GraphQLInputObjectType)
    assert copied_input_type is not input_type
    assert "field2" not in copied_input_type.fields
