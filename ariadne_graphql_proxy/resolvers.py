from graphql import GraphQLFieldResolver, GraphQLSchema


def set_resolver(
    schema: GraphQLSchema,
    type_name: str,
    field_name: str,
    resolver: GraphQLFieldResolver,
):
    schema.type_map[type_name].fields[field_name].resolve = resolver


def unset_resolver(
    schema: GraphQLSchema,
    type_name: str,
    field_name: str,
):
    schema.type_map[type_name].fields[field_name].resolve = None
