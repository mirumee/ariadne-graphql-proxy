import pytest
from graphql import (
    GraphQLField,
    GraphQLFloat,
    GraphQLInt,
    GraphQLObjectType,
    GraphQLString,
    GraphQLUnionType,
)

from ariadne_graphql_proxy.merge import merge_unions

type1 = GraphQLObjectType(
    name="Type1",
    fields={"val": GraphQLField(GraphQLFloat)},
)
type2 = GraphQLObjectType(
    name="Type2",
    fields={"field": GraphQLField(GraphQLInt)},
)
type3 = GraphQLObjectType(
    name="Type3",
    fields={"field": GraphQLField(GraphQLString)},
)
type4 = GraphQLObjectType(
    name="Type3",
    fields={"field": GraphQLField(GraphQLString)},
)

duplicated_type1 = GraphQLObjectType(
    name="Type1",
    fields={"val": GraphQLField(GraphQLFloat)},
)
merged_type1 = GraphQLObjectType(
    name="Type1",
    fields={"val": GraphQLField(GraphQLFloat)},
)
merged_type2 = GraphQLObjectType(
    name="Type2",
    fields={"field": GraphQLField(GraphQLInt)},
)
merged_type3 = GraphQLObjectType(
    name="Type3",
    fields={"field": GraphQLField(GraphQLString)},
)
merged_type4 = GraphQLObjectType(
    name="Type4",
    fields={"field": GraphQLField(GraphQLString)},
)


def test_merge_unions_returns_union_with_merged_types():
    union1 = GraphQLUnionType(name="TestUnion", types=(type1, type2))
    union2 = GraphQLUnionType(name="TestUnion", types=(duplicated_type1, type3))

    merged_union = merge_unions(
        {
            "Type1": merged_type1,
            "Type2": merged_type2,
            "Type3": merged_type3,
        },
        union1,
        union2,
    )

    assert isinstance(merged_union, GraphQLUnionType)
    assert merged_union is not union1
    assert merged_union is not union2
    assert len(merged_union.types) == 3
    assert merged_type1 in merged_union.types
    assert merged_type2 in merged_union.types
    assert merged_type3 in merged_union.types


def test_merge_unions_returns_union_with_description_from_first_union():
    union1 = GraphQLUnionType(
        name="TestUnion",
        types=(type1, type2),
        description="Hello world!",
    )
    union2 = GraphQLUnionType(
        name="TestUnion",
        types=(type3, type4),
    )

    merged_union = merge_unions(
        {
            "Type1": merged_type1,
            "Type2": merged_type2,
            "Type3": merged_type3,
            "Type4": merged_type4,
        },
        union1,
        union2,
    )

    assert isinstance(merged_union, GraphQLUnionType)
    assert merged_union.description == "Hello world!"


def test_merge_unions_returns_union_with_description_from_other_union():
    union1 = GraphQLUnionType(
        name="TestUnion",
        types=(type1, type2),
    )
    union2 = GraphQLUnionType(
        name="TestUnion",
        types=(type3, type4),
        description="Hello world!",
    )

    merged_union = merge_unions(
        {
            "Type1": merged_type1,
            "Type2": merged_type2,
            "Type3": merged_type3,
            "Type4": merged_type4,
        },
        union1,
        union2,
    )

    assert isinstance(merged_union, GraphQLUnionType)
    assert merged_union.description == "Hello world!"


def test_merge_unions_raises_type_error_for_not_matching_descriptions():
    union1 = GraphQLUnionType(
        name="TestUnion",
        types=(type1, type2),
        description="Lorem ipsum",
    )
    union2 = GraphQLUnionType(
        name="TestUnion",
        types=(type3, type4),
        description="Dolor met",
    )

    with pytest.raises(TypeError):
        merge_unions(
            {
                "Type1": merged_type1,
                "Type2": merged_type2,
                "Type3": merged_type3,
                "Type4": merged_type4,
            },
            union1,
            union2,
        )
