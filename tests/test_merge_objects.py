import pytest
from graphql import (
    GraphQLField,
    GraphQLFloat,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLString,
)

from ariadne_graphql_proxy import merge_objects


def test_merge_objects_returns_object_with_fields_from_both_objects():
    related_type = GraphQLObjectType(
        name="RelatedType", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    merged_related_type = GraphQLObjectType(
        name="RelatedType", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    object1 = GraphQLObjectType(
        name="TestType",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
            "fieldB": GraphQLField(type_=related_type),
        },
    )
    object2 = GraphQLObjectType(
        name="TestType",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
            "fieldC": GraphQLField(type_=GraphQLFloat),
        },
    )

    merged_object = merge_objects(
        merged_types={"RelatedType": merged_related_type},
        object1=object1,
        object2=object2,
    )

    assert isinstance(merged_object, GraphQLObjectType)
    assert merged_object.fields["fieldA"]
    assert merged_object.fields["fieldB"]
    assert merged_object.fields["fieldC"]


def test_merge_objects_returns_object_with_description_from_first_object():
    object1 = GraphQLObjectType(
        name="TestObject",
        description="Hello world!",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
        },
    )
    object2 = GraphQLObjectType(
        name="TestObject",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
        },
    )

    merged_object = merge_objects(
        merged_types={},
        object1=object1,
        object2=object2,
    )

    assert isinstance(merged_object, GraphQLObjectType)
    assert merged_object.description == "Hello world!"


def test_merge_objects_returns_object_with_description_from_other_object():
    object1 = GraphQLObjectType(
        name="TestObject",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
        },
    )
    object2 = GraphQLObjectType(
        name="TestObject",
        description="Hello world!",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
        },
    )

    merged_object = merge_objects(
        merged_types={},
        object1=object1,
        object2=object2,
    )

    assert isinstance(merged_object, GraphQLObjectType)
    assert merged_object.description == "Hello world!"


def test_merge_objects_raises_type_error_for_not_matching_descriptions():
    object1 = GraphQLObjectType(
        name="TestObject",
        description="Lorem ipsum",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
        },
    )
    object2 = GraphQLObjectType(
        name="TestObject",
        description="Dolor met",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
        },
    )

    with pytest.raises(TypeError):
        merge_objects(
            merged_types={},
            object1=object1,
            object2=object2,
        )


def test_merge_objects_returns_object_with_merged_implemented_interfaces():
    interface1 = GraphQLInterfaceType(
        name="TestInterface1", fields={"fieldA": GraphQLField(type_=GraphQLString)}
    )
    interface2 = GraphQLInterfaceType(
        name="TestInterface2", fields={"fieldA": GraphQLField(type_=GraphQLString)}
    )
    merged_interface1 = GraphQLInterfaceType(
        name="TestInterface1", fields={"fieldA": GraphQLField(type_=GraphQLString)}
    )
    merged_interface2 = GraphQLInterfaceType(
        name="TestInterface2", fields={"fieldA": GraphQLField(type_=GraphQLString)}
    )
    object1 = GraphQLObjectType(
        name="TestType",
        fields={"fieldA": GraphQLField(type_=GraphQLString)},
        interfaces=[interface1],
    )
    object2 = GraphQLObjectType(
        name="TestType",
        fields={"fieldA": GraphQLField(type_=GraphQLString)},
        interfaces=[interface2],
    )

    merged_object = merge_objects(
        merged_types={
            "TestInterface1": merged_interface1,
            "TestInterface2": merged_interface2,
        },
        object1=object1,
        object2=object2,
    )

    assert isinstance(merged_object, GraphQLObjectType)
    assert len(merged_object.interfaces) == 2
    assert {i.name for i in merged_object.interfaces} == {
        "TestInterface1",
        "TestInterface2",
    }
