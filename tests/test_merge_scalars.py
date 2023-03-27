import pytest
from graphql import GraphQLScalarType

from ariadne_graphql_proxy import merge_scalars


def test_merge_scalars_returns_merged_scalar():
    scalar1 = GraphQLScalarType(
        name="TestScalar", description="desc", specified_by_url="url"
    )
    scalar2 = GraphQLScalarType(
        name="TestScalar", description="desc", specified_by_url="url"
    )

    merged_scalar = merge_scalars(scalar1=scalar1, scalar2=scalar2)

    assert isinstance(merged_scalar, GraphQLScalarType)
    assert merged_scalar is not scalar1
    assert merged_scalar is not scalar2
    assert merged_scalar.name == scalar1.name
    assert merged_scalar.description == scalar1.description
    assert merged_scalar.specified_by_url == scalar1.specified_by_url


def test_merge_scalars_returns_scalar_with_description_from_first_scalar():
    scalar1 = GraphQLScalarType(
        name="TestScalar",
        description="Hello world!",
    )
    scalar2 = GraphQLScalarType(
        name="TestScalar",
    )

    merged_scalar = merge_scalars(scalar1, scalar2)

    assert isinstance(merged_scalar, GraphQLScalarType)
    assert merged_scalar.description == "Hello world!"


def test_merge_scalars_returns_scalar_with_description_from_other_scalar():
    scalar1 = GraphQLScalarType(
        name="TestScalar",
    )
    scalar2 = GraphQLScalarType(
        name="TestScalar",
        description="Hello world!",
    )

    merged_scalar = merge_scalars(scalar1, scalar2)

    assert isinstance(merged_scalar, GraphQLScalarType)
    assert merged_scalar.description == "Hello world!"


def test_merge_scalars_raises_type_error_for_not_matching_descriptions():
    scalar1 = GraphQLScalarType(
        name="TestScalar",
        description="Lorem ipsum",
    )
    scalar2 = GraphQLScalarType(
        name="TestScalar",
        description="Dolor met",
    )

    with pytest.raises(TypeError):
        merge_scalars(scalar1, scalar2)


def test_merge_scalars_returns_scalar_with_spec_url_from_first_scalar():
    scalar1 = GraphQLScalarType(
        name="TestScalar",
        specified_by_url="http://example.com/spec-1/",
    )
    scalar2 = GraphQLScalarType(
        name="TestScalar",
    )

    merged_scalar = merge_scalars(scalar1, scalar2)

    assert isinstance(merged_scalar, GraphQLScalarType)
    assert merged_scalar.specified_by_url == "http://example.com/spec-1/"


def test_merge_scalars_returns_scalar_with_spec_url_from_other_scalar():
    scalar1 = GraphQLScalarType(
        name="TestScalar",
    )
    scalar2 = GraphQLScalarType(
        name="TestScalar",
        specified_by_url="http://example.com/spec-1/",
    )

    merged_scalar = merge_scalars(scalar1, scalar2)

    assert isinstance(merged_scalar, GraphQLScalarType)
    assert merged_scalar.specified_by_url == "http://example.com/spec-1/"


def test_merge_scalars_raises_type_error_for_not_matching_spec_urls():
    scalar1 = GraphQLScalarType(
        name="TestScalar",
        specified_by_url="http://example.com/spec-1/",
    )
    scalar2 = GraphQLScalarType(
        name="TestScalar",
        specified_by_url="http://example.com/other-spec-2/",
    )

    with pytest.raises(TypeError):
        merge_scalars(scalar1, scalar2)
