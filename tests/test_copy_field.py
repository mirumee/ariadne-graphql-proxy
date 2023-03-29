from graphql import (
    GraphQLArgument,
    GraphQLField,
    GraphQLObjectType,
    GraphQLString,
)

from ariadne_graphql_proxy import copy_field


def test_copy_field_returns_new_field():
    graphql_field = GraphQLField(
        type_=GraphQLString,
        args={},
        resolve=lambda: None,
        subscribe=lambda: None,
        description="description",
        deprecation_reason="reason",
        extensions={"extension1": None},
    )

    copied_type = copy_field({}, graphql_field)

    assert isinstance(copied_type, GraphQLField)
    assert copied_type is not graphql_field
    assert copied_type.type == GraphQLString
    assert copied_type.args == {}
    assert copied_type.resolve == graphql_field.resolve
    assert copied_type.subscribe == graphql_field.subscribe
    assert copied_type.description == graphql_field.description
    assert copied_type.deprecation_reason == graphql_field.deprecation_reason
    assert copied_type.extensions == graphql_field.extensions


def test_copy_field_returns_new_field_with_related_type():
    related_type = GraphQLObjectType(
        name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    duplicated_related_type = GraphQLObjectType(
        name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    graphql_field = GraphQLField(type_=related_type)

    copied_type = copy_field({"TypeB": duplicated_related_type}, graphql_field)

    assert isinstance(copied_type, GraphQLField)
    assert copied_type is not graphql_field
    assert copied_type.type == duplicated_related_type


def test_copy_field_returns_field_without_excluded_arg():
    graphql_field = GraphQLField(
        type_=GraphQLString,
        args={
            "arg1": GraphQLArgument(type_=GraphQLString),
            "arg2": GraphQLArgument(type_=GraphQLString),
        },
    )

    copied_type = copy_field({}, graphql_field, field_exclude_args=["arg1"])

    assert isinstance(copied_type, GraphQLField)
    assert copied_type is not graphql_field
    assert "arg1" not in copied_type.args
