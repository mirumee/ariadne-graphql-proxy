from graphql import (
    GraphQLArgument,
    GraphQLField,
    GraphQLInt,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLString,
)

from ariadne_graphql_proxy import copy_object


def test_copy_object_returns_new_object_with_fields():
    related_type = GraphQLObjectType(
        name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    duplicated_related_type = GraphQLObjectType(
        name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    graphql_type = GraphQLObjectType(
        name="TypeName",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
            "fieldB": GraphQLField(type_=related_type),
        },
    )

    copied_type = copy_object({"TypeB": duplicated_related_type}, graphql_type)

    assert isinstance(copied_type, GraphQLObjectType)
    assert copied_type is not graphql_type
    assert copied_type.name == graphql_type.name
    assert copied_type.fields["fieldA"] is not graphql_type.fields["fieldA"]
    assert isinstance(copied_type.fields["fieldA"], GraphQLField)
    assert copied_type.fields["fieldA"].type == GraphQLString
    assert copied_type.fields["fieldB"] is not graphql_type.fields["fieldB"]
    assert isinstance(copied_type.fields["fieldB"], GraphQLField)
    assert copied_type.fields["fieldB"].type == duplicated_related_type


def test_copy_object_returns_new_object_with_implemented_interface():
    interface = GraphQLInterfaceType(
        name="TestInterface", fields={"fieldA": GraphQLField(type_=GraphQLString)}
    )
    duplicated_interface = GraphQLInterfaceType(
        name="TestInterface", fields={"fieldA": GraphQLField(type_=GraphQLString)}
    )
    graphql_type = GraphQLObjectType(
        name="TypeName",
        fields={"fieldA": GraphQLField(type_=GraphQLString)},
        interfaces=[interface],
    )

    copied_type = copy_object({"TestInterface": duplicated_interface}, graphql_type)

    assert isinstance(copied_type, GraphQLObjectType)
    assert copied_type is not graphql_type
    assert len(copied_type.interfaces) == 1
    assert copied_type.interfaces[0] is not interface
    assert copied_type.interfaces[0] is duplicated_interface


def test_copy_object_returns_new_object_without_excluded_field():
    graphql_type = GraphQLObjectType(
        name="TypeName",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
            "fieldB": GraphQLField(type_=GraphQLInt),
        },
    )

    copied_type = copy_object({}, graphql_type, object_exclude_fields=["fieldB"])

    assert isinstance(copied_type, GraphQLObjectType)
    assert copied_type is not graphql_type
    assert "fieldB" not in copied_type.fields


def test_copy_object_returns_new_object_without_excluded_argument():
    graphql_type = GraphQLObjectType(
        name="TypeName",
        fields={
            "fieldA": GraphQLField(
                type_=GraphQLString,
                args={
                    "arg1": GraphQLArgument(type_=GraphQLString),
                    "arg2": GraphQLArgument(type_=GraphQLString),
                },
            )
        },
    )

    copied_type = copy_object(
        {}, graphql_type, object_exclude_args={"fieldA": ["arg1"]}
    )

    assert isinstance(copied_type, GraphQLObjectType)
    assert copied_type is not graphql_type
    assert "arg1" not in copied_type.fields["fieldA"].args
