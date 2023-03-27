from graphql import GraphQLInputField, GraphQLInputObjectType, GraphQLString

from ariadne_graphql_proxy import copy_input_field


def test_copy_input_field_returns_new_input_field():
    graphql_field = GraphQLInputField(
        type_=GraphQLString,
        out_name="out_name",
        description="description",
        deprecation_reason="reason",
    )

    copied_type = copy_input_field({}, graphql_field)

    assert isinstance(copied_type, GraphQLInputField)
    assert copied_type is not graphql_field
    assert copied_type.type == GraphQLString
    assert copied_type.out_name == graphql_field.out_name
    assert copied_type.description == graphql_field.description
    assert copied_type.deprecation_reason == graphql_field.deprecation_reason


def test_copy_input_field_returns_new_input_field_with_related_type():
    related_type = GraphQLInputObjectType(
        name="TypeB", fields={"val": GraphQLInputField(type_=GraphQLString)}
    )
    duplicated_related_type = GraphQLInputObjectType(
        name="TypeB", fields={"val": GraphQLInputField(type_=GraphQLString)}
    )
    graphql_field = GraphQLInputField(type_=related_type)

    copied_type = copy_input_field({"TypeB": duplicated_related_type}, graphql_field)

    assert isinstance(copied_type, GraphQLInputField)
    assert copied_type is not graphql_field
    assert copied_type.type == duplicated_related_type
