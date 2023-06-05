from typing import Optional

from graphql import GraphQLFieldResolver, GraphQLSchema, GraphQLObjectType


def set_resolver(
    schema: GraphQLSchema,
    type_name: str,
    field_name: str,
    resolver: Optional[GraphQLFieldResolver],
):
    graphql_type = schema.type_map.get(type_name)
    if not graphql_type:
        raise ValueError(f"Type '{type_name}' doesn't exist in the schema.")
    if not isinstance(graphql_type, GraphQLObjectType):
        raise ValueError(
            f"Expected '{type_name}' to be a 'type', "
            f"found {type(graphql_type).__name__}."
        )
    if field_name not in graphql_type.fields:
        raise ValueError(
            f"Type '{type_name}' doesn't have a field named '{field_name}'."
        )

    graphql_type.fields[field_name].resolve = resolver


def unset_resolver(
    schema: GraphQLSchema,
    type_name: str,
    field_name: str,
):
    set_resolver(schema, type_name, field_name, None)
