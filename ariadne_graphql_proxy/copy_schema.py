from typing import Dict, List, Optional, Tuple

from graphql import (
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLDirective,
    GraphQLEnumType,
    GraphQLField,
    GraphQLFloat,
    GraphQLID,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInt,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNamedType,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLString,
    GraphQLUnionType,
)

from .standard_types import STANDARD_TYPES


def copy_schema(
    schema: GraphQLSchema,
    *,
    exclude_types: Optional[List[str]] = None,
    exclude_args: Optional[Dict[str, List[str]]] = None,
    exclude_fields: Optional[Dict[str, List[str]]] = None,
) -> GraphQLSchema:
    new_types = copy_schema_types(schema)

    query_type = None
    if schema.query_type:
        query_type = new_types[schema.query_type.name]

    mutation_type = None
    if schema.mutation_type:
        mutation_type = new_types[schema.mutation_type.name]

    return GraphQLSchema(
        query=query_type,
        mutation=mutation_type,
        types=new_types.values(),
        directives=copy_directives(new_types, schema.directives),
    )


def copy_schema_types(schema: GraphQLSchema):
    new_types = {}
    for graphql_type in schema.type_map.values():
        if graphql_type.name in STANDARD_TYPES:
            continue

        if isinstance(graphql_type, GraphQLEnumType):
            new_types[graphql_type.name] = copy_enum_type(graphql_type)

        if isinstance(graphql_type, GraphQLObjectType):
            new_types[graphql_type.name] = copy_object_type(new_types, graphql_type)

        if isinstance(graphql_type, GraphQLInputObjectType):
            new_types[graphql_type.name] = copy_input_type(new_types, graphql_type)

        if isinstance(graphql_type, GraphQLScalarType):
            new_types[graphql_type.name] = copy_scalar_type(graphql_type)

        if isinstance(graphql_type, GraphQLInterfaceType):
            new_types[graphql_type.name] = copy_interface_type(new_types, graphql_type)

        if isinstance(graphql_type, GraphQLUnionType):
            new_types[graphql_type.name] = copy_union_type(new_types, graphql_type)

    return new_types


def copy_enum_type(graphql_type):
    return GraphQLEnumType(
        graphql_type.name,
        graphql_type.values,
        description=graphql_type.description,
        extensions=graphql_type.extensions,
    )


def copy_object_type(new_types, graphql_type):
    def thunk():
        return {
            field_name: copy_field(new_types, field)
            for field_name, field in graphql_type.fields.items()
        }

    return GraphQLObjectType(
        graphql_type.name,
        thunk,
    )


def copy_field(new_types, graphql_field):
    return GraphQLField(
        copy_field_type(new_types, graphql_field.type),
        copy_arguments(new_types, graphql_field.args),
        graphql_field.resolve,
        graphql_field.subscribe,
        graphql_field.description,
        graphql_field.deprecation_reason,
        graphql_field.extensions.copy() if graphql_field.extensions else None,
    )


def copy_field_type(new_types, field_type):
    if isinstance(field_type, GraphQLList):
        return GraphQLList(copy_field_type(new_types, field_type.of_type))

    if isinstance(field_type, GraphQLNonNull):
        return GraphQLNonNull(copy_field_type(new_types, field_type.of_type))

    if field_type == GraphQLBoolean:
        return GraphQLBoolean
    if field_type == GraphQLString:
        return GraphQLString
    if field_type == GraphQLFloat:
        return GraphQLFloat
    if field_type == GraphQLID:
        return GraphQLID
    if field_type == GraphQLInt:
        return GraphQLInt

    if isinstance(
        field_type, (GraphQLEnumType, GraphQLObjectType, GraphQLInterfaceType)
    ):
        return new_types[field_type.name]

    raise Exception(f"Unknown field type: {repr(field_type)}")


def copy_arguments(new_types, field_args):
    if field_args == {}:
        return {}

    return {
        arg_name: GraphQLArgument(
            copy_argument_type(new_types, arg.type),
            default_value=arg.default_value,
            description=arg.description,
            deprecation_reason=arg.deprecation_reason,
            out_name=arg.out_name,
        )
        for arg_name, arg in field_args.items()
    }


def copy_argument_type(new_types, arg):
    if isinstance(arg, GraphQLList):
        return GraphQLList(copy_argument_type(new_types, arg.of_type))

    if isinstance(arg, GraphQLNonNull):
        return GraphQLNonNull(copy_argument_type(new_types, arg.of_type))

    if arg == GraphQLBoolean:
        return GraphQLBoolean
    if arg == GraphQLString:
        return GraphQLString
    if arg == GraphQLFloat:
        return GraphQLFloat
    if arg == GraphQLID:
        return GraphQLID
    if arg == GraphQLInt:
        return GraphQLInt

    if isinstance(arg, (GraphQLEnumType, GraphQLInputObjectType)):
        return new_types[arg.name]


def copy_input_type(new_types, graphql_type):
    def thunk():
        return {
            field_name: GraphQLInputField(
                copy_input_field_type(new_types, field.type),
                default_value=field.default_value,
                description=field.description,
                deprecation_reason=field.deprecation_reason,
                out_name=field.out_name,
            )
            for field_name, field in graphql_type.fields.items()
        }

    return GraphQLInputObjectType(
        graphql_type.name,
        thunk,
    )


def copy_input_field_type(new_types, field_type):
    if isinstance(field_type, GraphQLList):
        return GraphQLList(copy_input_field_type(new_types, field_type.of_type))

    if isinstance(field_type, GraphQLNonNull):
        return GraphQLNonNull(copy_input_field_type(new_types, field_type.of_type))

    if field_type == GraphQLBoolean:
        return GraphQLBoolean
    if field_type == GraphQLString:
        return GraphQLString
    if field_type == GraphQLFloat:
        return GraphQLFloat
    if field_type == GraphQLID:
        return GraphQLID
    if field_type == GraphQLInt:
        return GraphQLInt

    if isinstance(field_type, GraphQLNamedType):
        return new_types[field_type.name]


def copy_scalar_type(scalar):
    return GraphQLScalarType(
        name=scalar.name,
        serialize=scalar.serialize,
        parse_value=scalar.parse_value,
        parse_literal=scalar.parse_literal,
        description=scalar.description,
        specified_by_url=scalar.specified_by_url,
        extensions=scalar.extensions,
        ast_node=scalar.ast_node,
        extension_ast_nodes=scalar.extension_ast_nodes,
    )


def copy_interface_type(
    new_types: dict, interface_type: GraphQLInterfaceType
) -> GraphQLInterfaceType:
    def thunk():
        return {
            field_name: copy_field(new_types, field)
            for field_name, field in interface_type.fields.items()
        }

    return GraphQLInterfaceType(
        name=interface_type.name,
        fields=thunk,
    )


def copy_union_type(new_types: dict, union_type: GraphQLUnionType) -> GraphQLUnionType:
    def thunk():
        return tuple(new_types[subtype.name] for subtype in union_type.types)

    return GraphQLUnionType(name=union_type.name, types=thunk)


def copy_directives(
    new_types: dict, directives: Tuple[GraphQLDirective, ...]
) -> Tuple[GraphQLDirective, ...]:
    return tuple(copy_directive(new_types, directive) for directive in directives)


def copy_directive(new_types: dict, directive: GraphQLDirective) -> GraphQLDirective:
    return GraphQLDirective(
        name=directive.name,
        locations=directive.locations,
        args=copy_arguments(new_types, directive.args),
        is_repeatable=directive.is_repeatable,
        description=directive.description,
        extensions=directive.extensions.copy() if directive.extensions else {},
    )
