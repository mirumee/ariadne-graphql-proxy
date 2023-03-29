from graphql import GraphQLField, GraphQLObjectType, GraphQLString

from ariadne_graphql_proxy import merge_type_maps


def test_merge_type_maps_calls_copy_schema_type_if_object_is_not_present_in_one_map(
    mocker,
):
    mocked_copy_schema_type = mocker.patch(
        "ariadne_graphql_proxy.merge.copy_schema_type"
    )
    type_ = GraphQLObjectType(
        name="TypeName",
        fields={"fieldA": GraphQLField(type_=GraphQLString)},
    )

    merge_type_maps(type_map1={"TypeName": type_}, type_map2={})

    assert mocked_copy_schema_type.called
    assert mocked_copy_schema_type.called_with(new_types={}, graphql_type=type_)


def test_merge_type_maps_calls_merge_types_if_object_is_present_in_both_maps(
    mocker,
):
    mocked_merge_types = mocker.patch("ariadne_graphql_proxy.merge.merge_types")
    type1 = GraphQLObjectType(
        name="TypeName",
        fields={"fieldA": GraphQLField(type_=GraphQLString)},
    )
    type2 = GraphQLObjectType(
        name="TypeName",
        fields={"fieldA": GraphQLField(type_=GraphQLString)},
    )
    merge_type_maps(type_map1={"TypeName": type1}, type_map2={"TypeName": type2})

    assert mocked_merge_types.called
    assert mocked_merge_types.called_with(merge_types={}, type1=type1, type2=type2)
