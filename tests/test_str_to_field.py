import pytest
from graphql import (
    BooleanValueNode,
    FieldDefinitionNode,
    GraphQLArgument,
    GraphQLField,
    GraphQLNonNull,
    GraphQLScalarType,
    GraphQLSyntaxError,
    InputValueDefinitionNode,
    IntValueNode,
    NamedTypeNode,
    NonNullTypeNode,
    parse,
)

from ariadne_graphql_proxy.str_to_field import (
    get_field_definition_from_str,
    get_graphql_field_from_field_definition,
)


def test_get_field_definition_from_str_returns_field_definition_node():
    field_definition = get_field_definition_from_str("field: String!")

    assert isinstance(field_definition, FieldDefinitionNode)
    assert field_definition.name.value == "field"
    assert isinstance(field_definition.type, NonNullTypeNode)
    assert isinstance(field_definition.type.type, NamedTypeNode)
    assert field_definition.type.type.name.value == "String"


def test_get_field_definition_from_str_returns_node_with_nullable_type():
    field_definition = get_field_definition_from_str("nullableField: Int")

    assert isinstance(field_definition, FieldDefinitionNode)
    assert field_definition.name.value == "nullableField"
    assert isinstance(field_definition.type, NamedTypeNode)
    assert field_definition.type.name.value == "Int"


def test_get_field_definition_from_str_returns_node_with_arguments():
    field_definition = get_field_definition_from_str(
        "fieldWithArgs(arg1: Int, arg2: Boolean!): Float!"
    )

    assert isinstance(field_definition, FieldDefinitionNode)
    assert field_definition.name.value == "fieldWithArgs"
    assert isinstance(field_definition.type, NonNullTypeNode)
    assert isinstance(field_definition.type.type, NamedTypeNode)
    assert field_definition.type.type.name.value == "Float"

    arg1 = field_definition.arguments[0]
    assert arg1.name.value == "arg1"
    assert isinstance(arg1, InputValueDefinitionNode)
    assert isinstance(arg1.type, NamedTypeNode)
    assert arg1.type.name.value == "Int"

    arg2 = field_definition.arguments[1]
    assert arg2.name.value == "arg2"
    assert isinstance(arg2, InputValueDefinitionNode)
    assert isinstance(arg2.type, NonNullTypeNode)
    assert isinstance(arg2.type.type, NamedTypeNode)
    assert arg2.type.type.name.value == "Boolean"


def test_get_field_definition_from_str_returns_node_with_arguments_default_values():
    field_definition = get_field_definition_from_str(
        "fieldWithArgs(arg1: Int = 5, arg2: Boolean! = true): Float!"
    )

    assert isinstance(field_definition, FieldDefinitionNode)
    assert field_definition.name.value == "fieldWithArgs"
    assert isinstance(field_definition.type, NonNullTypeNode)
    assert isinstance(field_definition.type.type, NamedTypeNode)
    assert field_definition.type.type.name.value == "Float"

    arg1 = field_definition.arguments[0]
    assert arg1.name.value == "arg1"
    assert isinstance(arg1, InputValueDefinitionNode)
    assert isinstance(arg1.type, NamedTypeNode)
    assert arg1.type.name.value == "Int"
    assert isinstance(arg1.default_value, IntValueNode)
    assert arg1.default_value.value == "5"

    arg2 = field_definition.arguments[1]
    assert arg2.name.value == "arg2"
    assert isinstance(arg2, InputValueDefinitionNode)
    assert isinstance(arg2.type, NonNullTypeNode)
    assert isinstance(arg2.type.type, NamedTypeNode)
    assert arg2.type.type.name.value == "Boolean"
    assert isinstance(arg2.default_value, BooleanValueNode)
    assert arg2.default_value.value


def test_get_field_definition_from_str_returns_node_with_non_scalar_type():
    field_definition = get_field_definition_from_str("field: TestType!")

    assert isinstance(field_definition, FieldDefinitionNode)
    assert field_definition.name.value == "field"
    assert isinstance(field_definition.type, NonNullTypeNode)
    assert isinstance(field_definition.type.type, NamedTypeNode)
    assert field_definition.type.type.name.value == "TestType"


def test_get_field_definition_from_str_returns_node_with_input_type_argument():
    field_definition = get_field_definition_from_str("field(arg: TestInput): String")

    assert isinstance(field_definition, FieldDefinitionNode)
    assert field_definition.name.value == "field"
    assert isinstance(field_definition.type, NamedTypeNode)
    assert field_definition.type.name.value == "String"

    arg = field_definition.arguments[0]
    assert arg.name.value == "arg"
    assert isinstance(arg, InputValueDefinitionNode)
    assert isinstance(arg.type, NamedTypeNode)
    assert arg.type.name.value == "TestInput"


@pytest.mark.parametrize("invalid_str", ["", "field", "field String!"])
def test_get_field_definition_from_str_raises_graphql_syntax_error_for_invalid_str(
    invalid_str,
):
    with pytest.raises(GraphQLSyntaxError):
        get_field_definition_from_str(invalid_str)


def test_get_field_definition_from_str_raises_value_error_for_multiple_fields():
    with pytest.raises(ValueError):
        get_field_definition_from_str("fieldA: String!\nfieldB: Float!")


def test_get_graphql_field_from_field_definition_returns_graphql_field(schema):
    field_definition = parse("type A{ field: String! }").definitions[0].fields[0]

    graphql_field = get_graphql_field_from_field_definition(
        schema=schema, field_definition=field_definition
    )

    assert isinstance(graphql_field, GraphQLField)
    assert isinstance(graphql_field.type, GraphQLNonNull)
    assert isinstance(graphql_field.type.of_type, GraphQLScalarType)
    assert graphql_field.type.of_type.name == "String"


def test_get_graphql_field_from_field_definition_returns_field_with_nullable_type(
    schema,
):
    field_definition = parse("type A{ nullableField: Float }").definitions[0].fields[0]

    graphql_field = get_graphql_field_from_field_definition(
        schema=schema, field_definition=field_definition
    )

    assert isinstance(graphql_field, GraphQLField)
    assert isinstance(graphql_field.type, GraphQLScalarType)
    assert graphql_field.type.name == "Float"


def test_get_graphql_field_from_field_definition_returns_field_with_arguments(
    schema,
):
    field_definition = (
        parse("type A{ fieldWithArgs(arg1: Int, arg2: Boolean!): Float }")
        .definitions[0]
        .fields[0]
    )

    graphql_field = get_graphql_field_from_field_definition(
        schema=schema, field_definition=field_definition
    )

    assert isinstance(graphql_field, GraphQLField)
    assert isinstance(graphql_field.type, GraphQLScalarType)
    assert graphql_field.type.name == "Float"

    arg1 = graphql_field.args["arg1"]
    assert isinstance(arg1, GraphQLArgument)
    assert isinstance(arg1.type, GraphQLScalarType)
    assert arg1.type.name == "Int"

    arg2 = graphql_field.args["arg2"]
    assert isinstance(arg2, GraphQLArgument)
    assert isinstance(arg2.type, GraphQLNonNull)
    assert isinstance(arg2.type.of_type, GraphQLScalarType)
    assert arg2.type.of_type.name == "Boolean"


def test_get_graphql_field_from_field_definition_returns_arguments_with_default_values(
    schema,
):
    field_definition = (
        parse("type A{ fieldWithArgs(arg1: Int = 5, arg2: Boolean! = true): Float }")
        .definitions[0]
        .fields[0]
    )

    graphql_field = get_graphql_field_from_field_definition(
        schema=schema, field_definition=field_definition
    )

    assert isinstance(graphql_field, GraphQLField)
    assert isinstance(graphql_field.type, GraphQLScalarType)
    assert graphql_field.type.name == "Float"

    arg1 = graphql_field.args["arg1"]
    assert isinstance(arg1, GraphQLArgument)
    assert isinstance(arg1.type, GraphQLScalarType)
    assert arg1.type.name == "Int"
    assert arg1.default_value == 5

    arg2 = graphql_field.args["arg2"]
    assert isinstance(arg2, GraphQLArgument)
    assert isinstance(arg2.type, GraphQLNonNull)
    assert isinstance(arg2.type.of_type, GraphQLScalarType)
    assert arg2.type.of_type.name == "Boolean"
    assert arg2.default_value is True


def test_get_graphql_field_from_field_definition_returns_field_with_non_scalar_type(
    schema,
):
    field_definition = parse("type A{ field: Complex }").definitions[0].fields[0]

    graphql_field = get_graphql_field_from_field_definition(
        schema=schema, field_definition=field_definition
    )

    assert isinstance(graphql_field, GraphQLField)
    assert graphql_field.type is schema.type_map["Complex"]


def test_get_graphql_field_from_field_definition_returns_field_with_non_scalar_argument(
    schema,
):
    field_definition = (
        parse("type A{ field(arg: InputType): String }").definitions[0].fields[0]
    )

    graphql_field = get_graphql_field_from_field_definition(
        schema=schema, field_definition=field_definition
    )

    assert isinstance(graphql_field, GraphQLField)
    assert graphql_field.args["arg"].type is schema.type_map["InputType"]
