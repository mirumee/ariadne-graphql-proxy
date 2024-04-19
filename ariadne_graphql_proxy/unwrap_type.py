from typing import cast

from graphql import (
    GraphQLType,
    GraphQLNamedType,
    GraphQLWrappingType,
)


def unwrap_graphql_type(type_: GraphQLType) -> GraphQLNamedType:
    if isinstance(type_, GraphQLWrappingType):
        return unwrap_graphql_type(type_.of_type)

    return cast(GraphQLNamedType, type_)
