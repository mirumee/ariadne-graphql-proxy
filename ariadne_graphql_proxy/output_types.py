from graphql import GraphQLNamedOutputType, GraphQLOutputType, GraphQLWrappingType


def unwrap_output_type(type_: GraphQLOutputType) -> GraphQLNamedOutputType:
    if isinstance(type_, GraphQLWrappingType):
        return unwrap_output_type(type_.of_type)

    return type_
