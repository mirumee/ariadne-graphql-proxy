from typing import cast

from graphql import (
    FieldDefinitionNode,
    GraphQLArgument,
    GraphQLField,
    GraphQLInputType,
    GraphQLOutputType,
    GraphQLSchema,
    assert_input_type,
    assert_output_type,
    parse,
    type_from_ast,
    value_from_ast,
)


def get_field_definition_from_str(field_str: str) -> FieldDefinitionNode:
    document = parse(f"type Placeholder{{ {field_str} }}")

    if len(document.definitions) != 1:
        raise ValueError("Field str has to define 1 type.")

    definition = document.definitions[0]

    fields = getattr(definition, "fields", [])
    if len(fields) != 1:
        raise ValueError("Field str has to provide only 1 field.")

    return fields[0]


def get_graphql_field_from_field_definition(
    schema: GraphQLSchema, field_definition: FieldDefinitionNode
) -> GraphQLField:
    field_type = cast(GraphQLOutputType, type_from_ast(schema, field_definition.type))
    assert_output_type(field_type)

    field_args = {}
    for arg in field_definition.arguments:
        arg_type = cast(GraphQLInputType, type_from_ast(schema, arg.type))
        assert_input_type(arg_type)
        arg_default_value = value_from_ast(value_node=arg.default_value, type_=arg_type)

        field_args[arg.name.value] = GraphQLArgument(
            type_=arg_type,
            default_value=arg_default_value,
        )

    description = (
        None if not field_definition.description else field_definition.description.value
    )

    return GraphQLField(
        type_=field_type,
        args=field_args,
        description=description,
    )
