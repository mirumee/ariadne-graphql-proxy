import pytest
from graphql import GraphQLSchema, build_ast_schema, parse

from ariadne_graphql_proxy import copy_schema


def test_copy_schema_returns_new_schema_object_with_copied_query_and_mutation(gql):
    schema_str = gql(
        """
        schema {
            query: Query
            mutation: Mutation
        }

        type Query {
            testQuery: Int!
        }

        type Mutation {
            testMutation: String!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema)

    assert isinstance(copied_schema, GraphQLSchema)
    assert copied_schema is not schema
    assert copied_schema.query_type
    assert copied_schema.query_type is not schema.query_type
    assert copied_schema.mutation_type
    assert copied_schema.mutation_type is not schema.mutation_type


def test_copy_schema_returns_new_schema_object_with_copied_types(gql):
    schema_str = gql(
        """
        schema {
            query: Query
        }

        type Query {
            testQuery(input: TestInputB!): TestTypeA!
        }

        type TestTypeA {
            fieldA: Int!
        }

        input TestInputB {
            fieldb: String!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema)

    assert isinstance(copied_schema, GraphQLSchema)
    assert copied_schema is not schema
    assert copied_schema.type_map["TestTypeA"]
    assert copied_schema.type_map["TestTypeA"] is not schema.type_map["TestTypeA"]
    assert copied_schema.type_map["TestInputB"]
    assert copied_schema.type_map["TestInputB"] is not schema.type_map["TestInputB"]


def test_copy_schema_returns_new_schema_object_with_copied_directive(gql):
    schema_str = gql(
        """
        schema {
            query: Query
        }

        type Query {
            testQuery: Float!
        }

        directive @uppercase on FIELD_DEFINITION
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema)

    assert isinstance(copied_schema, GraphQLSchema)
    assert copied_schema is not schema
    org_directive = next(filter(lambda d: d.name == "uppercase", schema.directives))
    copied_directive = next(
        filter(lambda d: d.name == "uppercase", copied_schema.directives)
    )
    assert copied_directive
    assert copied_directive is not org_directive


def test_copy_schema_returns_new_schema_object_without_excluded_type(gql):
    schema_str = gql(
        """
        schema {
            query: Query
        }

        type Query {
            testQuery: TestTypeA!
        }

        type TestTypeA {
            fieldA: Int!
        }

        type TestTypeB {
            fieldB: String!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, exclude_types=["TestTypeB"])

    assert isinstance(copied_schema, GraphQLSchema)
    assert copied_schema is not schema
    assert "TestTypeB" not in copied_schema.type_map


def test_copy_schema_returns_new_schema_object_with_union_without_excluded_type(gql):
    schema_str = gql(
        """
        schema {
            query: Query
        }

        type Query {
            testQuery: TestTypeA!
        }

        type TestTypeA {
            fieldA: Int!
        }

        type TestTypeB {
            fieldB: String!
        }

        union TestUnionType = TestTypeA | TestTypeB
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, exclude_types=["TestTypeB"])

    assert isinstance(copied_schema, GraphQLSchema)
    assert copied_schema is not schema
    assert "TestTypeB" not in copied_schema.type_map
    assert len(copied_schema.type_map["TestUnionType"].types) == 1
    assert copied_schema.type_map["TestUnionType"].types[0].name == "TestTypeA"


def test_copy_schema_raises_exception_if_excluded_type_is_used_by_not_excluded_field(
    gql,
):
    schema_str = gql(
        """
        schema {
            query: Query
        }

        type Query {
            testQuery: TestTypeA!
        }

        type TestTypeA {
            fieldA: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    with pytest.raises(TypeError):
        copy_schema(schema, exclude_types=["TestTypeA"])


def test_copy_schema_doesnt_raise_exception_if_type_is_excluded_with_fields_of_type(
    gql,
):
    schema_str = gql(
        """
        schema {
            query: Query
        }

        type Query {
            testQuery: TestTypeA!
        }

        type TestTypeA {
            fieldA: Int!
            fieldB: TestTypeB!
        }

        type TestTypeB {
            id: ID!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema,
        exclude_types=["TestTypeB"],
        exclude_fields={"TestTypeA": ["fieldB"]},
    )

    assert isinstance(copied_schema, GraphQLSchema)
    assert copied_schema is not schema


def test_copy_schema_raises_exception_if_excluded_type_is_used_by_not_excluded_arg(
    gql,
):
    schema_str = gql(
        """
        schema {
            query: Query
        }

        type Query {
            testQuery(input: TestInputA!): Int!
        }

        input TestInputA {
            fieldA: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    with pytest.raises(TypeError):
        copy_schema(schema, exclude_types=["TestInputA"])


def test_copy_schema_doesnt_raise_exception_if_type_is_excluded_with_arg_of_type(
    gql,
):
    schema_str = gql(
        """
        schema {
            query: Query
        }

        type Query {
            testQuery(input: TestInputA!): Int!
        }

        input TestInputA {
            fieldA: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema,
        exclude_types=["TestInputA"],
        exclude_args={"Query": {"testQuery": ["input"]}},
    )

    assert isinstance(copied_schema, GraphQLSchema)
    assert copied_schema is not schema


def test_copy_schema_with_field_returning_custom_scalars(gql):
    schema_str = gql(
        """
        scalar Custom

        type Query {
            testQuery: Custom!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))
    copied_schema = copy_schema(schema)

    assert isinstance(copied_schema, GraphQLSchema)
    assert copied_schema is not schema
    assert "Custom" in copied_schema.type_map


def test_copy_schema_with_field_arguments_as_custom_scalars(gql):
    schema_str = gql(
        """
        scalar Custom

        type Query {
            testQuery(arg: Custom!): String!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))
    copied_schema = copy_schema(schema)

    assert isinstance(copied_schema, GraphQLSchema)
    assert copied_schema is not schema
    assert "Custom" in copied_schema.type_map


def test_copy_schema_with_field_returning_union_type(gql):
    schema_str = gql(
        """
        type Query {
            testQuery: Result!
        }

        type User {
            id: ID!
            name: String!
        }

        type Comment {
            id: ID!
            message: String!
        }

        union Result = User | Comment
        """
    )
    schema = build_ast_schema(parse(schema_str))
    copied_schema = copy_schema(schema)

    assert isinstance(copied_schema, GraphQLSchema)
    assert copied_schema is not schema
    assert "Result" in copied_schema.type_map
