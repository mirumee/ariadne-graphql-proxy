from graphql import (
    GraphQLField,
    GraphQLObjectType,
    GraphQLString,
    GraphQLUnionType,
)

from ariadne_graphql_proxy import copy_union


def test_copy_union_returns_copy_of_union_with_copies_of_subtypes():
    subtype1 = GraphQLObjectType(
        name="TypeA", fields={"valA": GraphQLField(type_=GraphQLString)}
    )
    duplicated_subtype1 = GraphQLObjectType(
        name="TypeA", fields={"valA": GraphQLField(type_=GraphQLString)}
    )
    subtype2 = GraphQLObjectType(
        name="TypeB", fields={"valB": GraphQLField(type_=GraphQLString)}
    )
    duplicated_subtype2 = GraphQLObjectType(
        name="TypeB", fields={"valB": GraphQLField(type_=GraphQLString)}
    )
    union_type = GraphQLUnionType(name="UnionType", types=[subtype1, subtype2])

    copied_union_type = copy_union(
        {"TypeA": duplicated_subtype1, "TypeB": duplicated_subtype2}, union_type
    )

    assert isinstance(copied_union_type, GraphQLUnionType)
    assert copied_union_type is not union_type
    assert copied_union_type.types == (duplicated_subtype1, duplicated_subtype2)
