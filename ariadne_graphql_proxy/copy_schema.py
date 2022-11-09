from dataclasses import field
from graphql import (
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLEnumType,
    GraphQLField,
    GraphQLFloat,
    GraphQLID,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInt,
    GraphQLList,
    GraphQLNamedType,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
)

from .standard_types import STANDARD_TYPES


def copy_schema(schema: GraphQLSchema) -> GraphQLSchema:
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
            field_name: copy_object_field(new_types, field)
            for field_name, field in graphql_type.fields.items()
        }

    return GraphQLObjectType(
        graphql_type.name,
        thunk,
    )


def copy_object_field(new_types, graphql_field):
    return GraphQLField(
        copy_object_field_type(new_types, graphql_field.type),
        copy_object_field_args(new_types, graphql_field.args),
        graphql_field.resolve,
        graphql_field.subscribe,
        graphql_field.description,
        graphql_field.deprecation_reason,
        graphql_field.extensions.copy() if graphql_field.extensions else None,
    )


def copy_object_field_type(new_types, field_type):
    if isinstance(field_type, GraphQLList):
        return GraphQLList(copy_object_field_type(new_types, field_type.of_type))

    if isinstance(field_type, GraphQLNonNull):
        return GraphQLNonNull(copy_object_field_type(new_types, field_type.of_type))

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

    if isinstance(field_type, (GraphQLEnumType, GraphQLObjectType)):
        return new_types[field_type.name]

    raise Exception(f"Unknown field type: {repr(field_type)}")


def copy_object_field_args(new_types, field_args):
    if field_args == {}:
        return {}

    return {
        arg_name: GraphQLArgument(
            copy_object_field_arg(new_types, arg.type),
            default_value=arg.default_value,
            description=arg.description,
            deprecation_reason=arg.deprecation_reason,
            out_name=arg.out_name,
        )
        for arg_name, arg in field_args.items()
    }


def copy_object_field_arg(new_types, arg):
    if isinstance(arg, GraphQLList):
        return GraphQLList(copy_object_field_arg(new_types, arg.of_type))

    if isinstance(arg, GraphQLNonNull):
        return GraphQLNonNull(copy_object_field_arg(new_types, arg.of_type))

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
                copy_input_field(new_types, field.type),
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


def copy_input_field(new_types, field_type):
    if isinstance(field_type, GraphQLList):
        return GraphQLList(copy_input_field(new_types, field_type.of_type))

    if isinstance(field_type, GraphQLNonNull):
        return GraphQLNonNull(copy_input_field(new_types, field_type.of_type))

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
