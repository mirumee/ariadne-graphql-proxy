import pytest
from graphql import (
    GraphQLField,
    GraphQLFloat,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLString,
)

from ariadne_graphql_proxy.merge import merge_interfaces


def test_merge_interfaces_returns_interface_with_fields_from_both_interfaces():
    related_type = GraphQLObjectType(
        name="RelatedType", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    merged_related_type = GraphQLObjectType(
        name="RelatedType", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    interface1 = GraphQLInterfaceType(
        name="TestInterface",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
            "fieldB": GraphQLField(type_=related_type),
        },
    )
    interface2 = GraphQLInterfaceType(
        name="TestInput",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
            "fieldC": GraphQLField(type_=GraphQLFloat),
        },
    )

    merged_interface = merge_interfaces(
        merged_types={"RelatedType": merged_related_type},
        interface1=interface1,
        interface2=interface2,
    )

    assert isinstance(merged_interface, GraphQLInterfaceType)
    assert merged_interface.fields["fieldA"]
    assert merged_interface.fields["fieldB"]
    assert merged_interface.fields["fieldC"]


def test_merge_interfaces_returns_interface_with_merged_implemented_interfaces():
    implemented_interface1 = GraphQLInterfaceType(
        name="TestInterface1", fields={"fieldA": GraphQLField(type_=GraphQLString)}
    )
    implemented_interface2 = GraphQLInterfaceType(
        name="TestInterface2", fields={"fieldA": GraphQLField(type_=GraphQLString)}
    )
    merged_implemented_interface1 = GraphQLInterfaceType(
        name="TestInterface1", fields={"fieldA": GraphQLField(type_=GraphQLString)}
    )
    merged_implemented_interface2 = GraphQLInterfaceType(
        name="TestInterface2", fields={"fieldA": GraphQLField(type_=GraphQLString)}
    )
    interface1 = GraphQLInterfaceType(
        name="TestInterface",
        fields={"fieldA": GraphQLField(type_=GraphQLString)},
        interfaces=[implemented_interface1],
    )
    interface2 = GraphQLInterfaceType(
        name="TestType",
        fields={"fieldA": GraphQLField(type_=GraphQLString)},
        interfaces=[implemented_interface2],
    )

    merged_interface = merge_interfaces(
        merged_types={
            "TestInterface1": merged_implemented_interface1,
            "TestInterface2": merged_implemented_interface2,
        },
        interface1=interface1,
        interface2=interface2,
    )

    assert isinstance(merged_interface, GraphQLInterfaceType)
    assert len(merged_interface.interfaces) == 2
    assert {i.name for i in merged_interface.interfaces} == {
        "TestInterface1",
        "TestInterface2",
    }


def test_merge_interfaces_returns_interface_with_description_from_first_interface():
    interface1 = GraphQLInterfaceType(
        name="TestInterface",
        description="Hello world!",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
        },
    )
    interface2 = GraphQLInterfaceType(
        name="TestInterface",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
        },
    )

    merged_interface = merge_interfaces(
        merged_types={},
        interface1=interface1,
        interface2=interface2,
    )

    assert isinstance(merged_interface, GraphQLInterfaceType)
    assert merged_interface.description == "Hello world!"


def test_merge_interfaces_returns_interface_with_description_from_other_interface():
    interface1 = GraphQLInterfaceType(
        name="TestInterface",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
        },
    )
    interface2 = GraphQLInterfaceType(
        name="TestInterface",
        description="Hello world!",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
        },
    )

    merged_interface = merge_interfaces(
        merged_types={},
        interface1=interface1,
        interface2=interface2,
    )

    assert isinstance(merged_interface, GraphQLInterfaceType)
    assert merged_interface.description == "Hello world!"


def test_merge_interfaces_raises_type_error_for_not_matching_descriptions():
    interface1 = GraphQLInterfaceType(
        name="TestInterface",
        description="Lorem ipsum",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
        },
    )
    interface2 = GraphQLInterfaceType(
        name="TestInterface",
        description="Dolor met",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
        },
    )

    with pytest.raises(TypeError):
        merge_interfaces(
            merged_types={},
            interface1=interface1,
            interface2=interface2,
        )
