from textwrap import dedent

import pytest
from graphql import GraphQLError, parse

from ariadne_graphql_proxy import print_document


def test_simple_document_is_printed():
    document = parse("{ hello }")
    assert (
        print_document(document)
        == dedent(
            """
        query {
          hello
        }
        """
        ).strip()
    )


def test_document_with_named_operation_is_printed():
    document = parse("query GetHello { hello }")
    assert (
        print_document(document)
        == dedent(
            """
        query GetHello {
          hello
        }
        """
        ).strip()
    )


def test_document_with_nested_fields_is_printed():
    document = parse(
        """
        {
            user {
                id
                name
                group {
                    id
                    name
                    title
                }
                rank
                email
            }
            ranks
        }
        """
    )
    assert (
        print_document(document)
        == dedent(
            """
        query {
          user {
            id
            name
            group {
              id
              name
              title
            }
            rank
            email
          }
          ranks
        }
        """
        ).strip()
    )


def test_document_with_alias_field_is_printed():
    document = parse("query { greeting: hello }")
    assert (
        print_document(document)
        == dedent(
            """
        query {
          greeting: hello
        }
        """
        ).strip()
    )


def test_document_with_named_operation_and_single_var_is_printed():
    document = parse("query GetHello($name: String!) {hello(name: $name) }")
    assert (
        print_document(document)
        == dedent(
            """
        query GetHello($name: String!) {
          hello(name: $name)
        }
        """
        ).strip()
    )


def test_document_with_named_operation_and_multiple_vars_is_printed():
    document = parse(
        """
        query GetHello($name: String!, $age: Int!) {
            hello(name: $name, age: $age)
        }
        """
    )
    assert (
        print_document(document)
        == dedent(
            """
        query GetHello($name: String!, $age: Int!) {
          hello(name: $name, age: $age)
        }
        """
        ).strip()
    )


def test_document_with_named_operation_and_multiple_fields_and_args_is_printed():
    document = parse(
        """
        query GetHello($name: String!) {
            hello(name: $name, age: 21, birthplace: null)
        }
        """
    )
    assert (
        print_document(document)
        == dedent(
            """
        query GetHello($name: String!) {
          hello(name: $name, age: 21, birthplace: null)
        }
        """
        ).strip()
    )


def test_document_with_variable_arg_is_printed():
    document = parse("{ hello(name: $variable) }")
    assert (
        print_document(document)
        == dedent(
            """
        query {
          hello(name: $variable)
        }
        """
        ).strip()
    )


def test_document_with_list_arg_is_printed():
    document = parse("{ hello(names: [1, 2, 3, 4]) }")
    assert (
        print_document(document)
        == dedent(
            """
        query {
          hello(names: [1, 2, 3, 4])
        }
        """
        ).strip()
    )


def test_document_with_null_arg_is_printed():
    document = parse("{ hello(name: null) }")
    assert (
        print_document(document)
        == dedent(
            """
        query {
          hello(name: null)
        }
        """
        ).strip()
    )


def test_document_with_enum_arg_is_printed():
    document = parse("{ hello(name: ADMIN) }")
    assert (
        print_document(document)
        == dedent(
            """
        query {
          hello(name: ADMIN)
        }
        """
        ).strip()
    )


def test_document_with_bool_true_arg_is_printed():
    document = parse("{ hello(name: true) }")
    assert (
        print_document(document)
        == dedent(
            """
        query {
          hello(name: true)
        }
        """
        ).strip()
    )


def test_document_with_bool_false_arg_is_printed():
    document = parse("{ hello(name: false) }")
    assert (
        print_document(document)
        == dedent(
            """
        query {
          hello(name: false)
        }
        """
        ).strip()
    )


def test_document_with_object_arg_is_printed():
    document = parse("{ hello(name: { from: 12, to: true }) }")
    assert (
        print_document(document)
        == dedent(
            """
        query {
          hello(name: { from: 12, to: true })
        }
        """
        ).strip()
    )


def test_document_with_string_arg_is_printed():
    document = parse('{ hello(name: "John") }')
    assert (
        print_document(document)
        == dedent(
            """
        query {
          hello(name: \"John\")
        }
        """
        ).strip()
    )


def test_document_with_block_string_arg_is_printed():
    document = parse('{ hello(name: """John""") }')
    assert (
        print_document(document)
        == dedent(
            """
        query {
          hello(name: \"\"\"John\"\"\")
        }
        """
        ).strip()
    )


def test_document_with_string_arg_containing_quotes_is_printed():
    document = parse('{ hello(name: "John \\"doe\\"") }')
    assert (
        print_document(document)
        == dedent(
            """
        query {
          hello(name: \"John \\"doe\\"")
        }
        """
        ).strip()
    )


def test_document_with_fragments_is_printed():
    document = parse(
        """
        query GetHello {
            ...UserData
        }

        fragment UserData on User {
            id
            email
        }
        """
    )
    assert (
        print_document(document)
        == dedent(
            """
        query GetHello {
          ...UserData
        }

        fragment UserData on User {
          id
          email
        }
        """
        ).strip()
    )


def test_document_with_multiple_operations_is_printed():
    document = parse(
        """
        query getUser {
            user
        }

        query getCategory {
            category
        }
        """
    )
    assert (
        print_document(document)
        == dedent(
            """
        query getUser {
          user
        }

        query getCategory {
          category
        }
        """
        ).strip()
    )


def test_selected_operation_in_document_is_printed():
    document = parse(
        """
        query getUser {
            user
        }

        query getCategory {
            category
        }
        """
    )
    assert (
        print_document(document, operation_name="getCategory")
        == dedent(
            """
        query getCategory {
          category
        }
        """
        ).strip()
    )


def test_printing_wrong_operation_from_document_raises_error():
    document = parse(
        """
        query getUser {
            user
        }

        query getCategory {
            category
        }
        """
    )

    with pytest.raises(GraphQLError) as excinfo:
        print_document(document, operation_name="getProducts")

    assert "Unknown operation named 'getProducts'." == str(excinfo.value)
