from graphql import GraphQLBoolean, GraphQLFloat, GraphQLID, GraphQLInt, GraphQLString

STANDARD_TYPES = (
    "ID",
    "Boolean",
    "Float",
    "Int",
    "String",
    "__Schema",
    "__Type",
    "__TypeKind",
    "__Field",
    "__InputValue",
    "__EnumValue",
    "__Directive",
    "__DirectiveLocation",
)


def add_missing_scalar_types(schema_types: dict) -> dict:
    scalar_types = {
        "ID": GraphQLID,
        "Boolean": GraphQLBoolean,
        "Float": GraphQLFloat,
        "Int": GraphQLInt,
        "String": GraphQLString,
    }
    scalar_types.update(schema_types)
    return scalar_types
