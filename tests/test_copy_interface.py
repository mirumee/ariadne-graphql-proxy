from graphql import (
    GraphQLArgument,
    GraphQLField,
    GraphQLID,
    GraphQLInterfaceType,
    GraphQLString,
)

from ariadne_graphql_proxy import copy_interface


def test_copy_interface_returns_new_object_with_fields():
    related_type = GraphQLInterfaceType(
        name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    duplicated_related_type = GraphQLInterfaceType(
        name="TypeB", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    graphql_type = GraphQLInterfaceType(
        name="TypeName",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
            "fieldB": GraphQLField(type_=related_type),
        },
    )

    copied_type = copy_interface({"TypeB": duplicated_related_type}, graphql_type)

    assert isinstance(copied_type, GraphQLInterfaceType)
    assert copied_type is not graphql_type
    assert copied_type.name == graphql_type.name
    assert copied_type.fields["fieldA"] is not graphql_type.fields["fieldA"]
    assert isinstance(copied_type.fields["fieldA"], GraphQLField)
    assert copied_type.fields["fieldA"].type == GraphQLString
    assert copied_type.fields["fieldB"] is not graphql_type.fields["fieldB"]
    assert isinstance(copied_type.fields["fieldB"], GraphQLField)
    assert copied_type.fields["fieldB"].type == duplicated_related_type


def test_copy_interface_returns_new_interface_without_excluded_fields():
    graphql_type = GraphQLInterfaceType(
        name="TypeName",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
            "fieldB": GraphQLField(type_=GraphQLID),
        },
    )

    copied_type = copy_interface({}, graphql_type, object_exclude_fields=["fieldB"])

    assert isinstance(copied_type, GraphQLInterfaceType)
    assert copied_type is not graphql_type
    assert "fieldB" not in copied_type.fields


def test_copy_interface_returns_new_interface_without_excluded_arg():
    graphql_type = GraphQLInterfaceType(
        name="TypeName",
        fields={
            "fieldA": GraphQLField(
                type_=GraphQLString,
                args={
                    "arg1": GraphQLArgument(type_=GraphQLString),
                    "arg2": GraphQLArgument(type_=GraphQLString),
                },
            ),
        },
    )

    copied_type = copy_interface(
        {}, graphql_type, object_exclude_args={"fieldA": ["arg1"]}
    )

    assert isinstance(copied_type, GraphQLInterfaceType)
    assert copied_type is not graphql_type
    assert "arg1" not in copied_type.fields["fieldA"].args
