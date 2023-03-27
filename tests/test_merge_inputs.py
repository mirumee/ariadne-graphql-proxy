import pytest
from graphql import (
    GraphQLFloat,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLString,
)

from ariadne_graphql_proxy import merge_inputs


def test_merge_inputs_returns_input_with_fields_from_both_inputs():
    related_input = GraphQLInputObjectType(
        name="RelatedInput", fields={"val": GraphQLInputField(type_=GraphQLString)}
    )
    merged_related_input = GraphQLInputObjectType(
        name="RelatedInput", fields={"val": GraphQLInputField(type_=GraphQLString)}
    )
    input1 = GraphQLInputObjectType(
        name="TestInput",
        fields={
            "fieldA": GraphQLInputField(type_=GraphQLString),
            "fieldB": GraphQLInputField(type_=related_input),
        },
    )
    input2 = GraphQLInputObjectType(
        name="TestInput",
        fields={
            "fieldA": GraphQLInputField(type_=GraphQLString),
            "fieldC": GraphQLInputField(type_=GraphQLFloat),
        },
    )

    merged_input = merge_inputs(
        merged_types={"RelatedInput": merged_related_input},
        input1=input1,
        input2=input2,
    )

    assert isinstance(merged_input, GraphQLInputObjectType)
    assert merged_input.fields["fieldA"]
    assert merged_input.fields["fieldB"]
    assert merged_input.fields["fieldC"]


def test_merge_inputs_returns_input_with_description_from_first_input():
    input1 = GraphQLInputObjectType(
        name="TestInput",
        description="Hello world!",
        fields={
            "fieldA": GraphQLInputField(type_=GraphQLString),
        },
    )
    input2 = GraphQLInputObjectType(
        name="TestInput",
        fields={
            "fieldA": GraphQLInputField(type_=GraphQLString),
        },
    )

    merged_input = merge_inputs(
        merged_types={},
        input1=input1,
        input2=input2,
    )

    assert isinstance(merged_input, GraphQLInputObjectType)
    assert merged_input.description == "Hello world!"


def test_merge_inputs_returns_input_with_description_from_other_input():
    input1 = GraphQLInputObjectType(
        name="TestInput",
        fields={
            "fieldA": GraphQLInputField(type_=GraphQLString),
        },
    )
    input2 = GraphQLInputObjectType(
        name="TestInput",
        description="Hello world!",
        fields={
            "fieldA": GraphQLInputField(type_=GraphQLString),
        },
    )

    merged_input = merge_inputs(
        merged_types={},
        input1=input1,
        input2=input2,
    )

    assert isinstance(merged_input, GraphQLInputObjectType)
    assert merged_input.description == "Hello world!"


def test_merge_inputs_raises_type_error_for_not_matching_descriptions():
    input1 = GraphQLInputObjectType(
        name="TestInput",
        description="Lorem ipsum",
        fields={
            "fieldA": GraphQLInputField(type_=GraphQLString),
        },
    )
    input2 = GraphQLInputObjectType(
        name="TestInput",
        description="Dolor met",
        fields={
            "fieldA": GraphQLInputField(type_=GraphQLString),
        },
    )

    with pytest.raises(TypeError):
        merge_inputs(
            merged_types={},
            input1=input1,
            input2=input2,
        )


def input_out_type_a():
    pass


def input_out_type_b():
    pass


def test_merge_inputs_returns_input_with_out_type_from_first_input():
    input1 = GraphQLInputObjectType(
        name="TestInput",
        out_type=input_out_type_a,
        fields={
            "fieldA": GraphQLInputField(type_=GraphQLString),
        },
    )
    input2 = GraphQLInputObjectType(
        name="TestInput",
        fields={
            "fieldA": GraphQLInputField(type_=GraphQLString),
        },
    )

    merged_input = merge_inputs(
        merged_types={},
        input1=input1,
        input2=input2,
    )

    assert isinstance(merged_input, GraphQLInputObjectType)
    assert merged_input.out_type == input_out_type_a


def test_merge_inputs_returns_input_with_out_type_from_other_input():
    input1 = GraphQLInputObjectType(
        name="TestInput",
        fields={
            "fieldA": GraphQLInputField(type_=GraphQLString),
        },
    )
    input2 = GraphQLInputObjectType(
        name="TestInput",
        out_type=input_out_type_b,
        fields={
            "fieldA": GraphQLInputField(type_=GraphQLString),
        },
    )

    merged_input = merge_inputs(
        merged_types={},
        input1=input1,
        input2=input2,
    )

    assert isinstance(merged_input, GraphQLInputObjectType)
    assert merged_input.out_type == input_out_type_b


def test_merge_inputs_raises_type_error_for_not_matching_out_types():
    input1 = GraphQLInputObjectType(
        name="TestInput",
        out_type=input_out_type_a,
        fields={
            "fieldA": GraphQLInputField(type_=GraphQLString),
        },
    )
    input2 = GraphQLInputObjectType(
        name="TestInput",
        out_type=input_out_type_b,
        fields={
            "fieldA": GraphQLInputField(type_=GraphQLString),
        },
    )

    with pytest.raises(TypeError):
        merge_inputs(
            merged_types={},
            input1=input1,
            input2=input2,
        )
