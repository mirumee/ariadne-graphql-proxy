from textwrap import dedent

import pytest
from graphql import parse

from ariadne_graphql_proxy import print_document
from ariadne_graphql_proxy.exceptions import InvalidOperationNameError


def test_simple_query_is_printed():
    query_document = parse("{ hello }")
    assert (
        print_document(query_document)
        == dedent(
            """
        query {
          hello
        }
        """
        ).strip()
    )


def test_query_with_name_is_printed():
    query_document = parse("query GetHello { hello }")
    assert (
        print_document(query_document)
        == dedent(
            """
        query GetHello {
          hello
        }
        """
        ).strip()
    )


def test_query_with_nested_fields_is_printed():
    query_document = parse(
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
        print_document(query_document)
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


def test_query_with_alias_field_is_printed():
    query_document = parse("query { greeting: hello }")
    assert (
        print_document(query_document)
        == dedent(
            """
        query {
          greeting: hello
        }
        """
        ).strip()
    )


def test_query_with_name_and_single_var_is_printed():
    query_document = parse("query GetHello($name: String!) {hello(name: $name) }")
    assert (
        print_document(query_document)
        == dedent(
            """
        query GetHello($name: String!) {
          hello(name: $name)
        }
        """
        ).strip()
    )


def test_query_with_name_and_multiple_vars_is_printed():
    query_document = parse(
        """
        query GetHello($name: String!, $age: Int!) {
            hello(name: $name, age: $age)
        }
        """
    )
    assert (
        print_document(query_document)
        == dedent(
            """
        query GetHello($name: String!, $age: Int!) {
          hello(name: $name, age: $age)
        }
        """
        ).strip()
    )


def test_query_with_name_and_multiple_fields_and_args_is_printed():
    query_document = parse(
        """
        query GetHello($name: String!) {
            hello(name: $name, age: 21, birthplace: null)
        }
        """
    )
    assert (
        print_document(query_document)
        == dedent(
            """
        query GetHello($name: String!) {
          hello(name: $name, age: 21, birthplace: null)
        }
        """
        ).strip()
    )


def test_query_with_variable_arg_is_printed():
    query_document = parse("{ hello(name: $name) }")
    assert (
        print_document(query_document)
        == dedent(
            """
        query {
          hello(name: $name)
        }
        """
        ).strip()
    )


def test_query_with_list_arg_is_printed():
    query_document = parse("{ hello(names: [1, 2, 3, 4]) }")
    assert (
        print_document(query_document)
        == dedent(
            """
        query {
          hello(names: [1, 2, 3, 4])
        }
        """
        ).strip()
    )


def test_query_with_null_arg_is_printed():
    query_document = parse("{ hello(name: null) }")
    assert (
        print_document(query_document)
        == dedent(
            """
        query {
          hello(name: null)
        }
        """
        ).strip()
    )


def test_query_with_enum_arg_is_printed():
    query_document = parse("{ hello(name: ADMIN) }")
    assert (
        print_document(query_document)
        == dedent(
            """
        query {
          hello(name: ADMIN)
        }
        """
        ).strip()
    )


def test_query_with_bool_true_arg_is_printed():
    query_document = parse("{ hello(name: true) }")
    assert (
        print_document(query_document)
        == dedent(
            """
        query {
          hello(name: true)
        }
        """
        ).strip()
    )


def test_query_with_bool_false_arg_is_printed():
    query_document = parse("{ hello(name: false) }")
    assert (
        print_document(query_document)
        == dedent(
            """
        query {
          hello(name: false)
        }
        """
        ).strip()
    )


def test_query_with_object_arg_is_printed():
    query_document = parse("{ hello(name: { from: 12, to: true }) }")
    assert (
        print_document(query_document)
        == dedent(
            """
        query {
          hello(name: { from: 12, to: true })
        }
        """
        ).strip()
    )


def test_query_with_string_arg_is_printed():
    query_document = parse('{ hello(name: "John") }')
    assert (
        print_document(query_document)
        == dedent(
            """
        query {
          hello(name: \"John\")
        }
        """
        ).strip()
    )


def test_query_with_block_string_arg_is_printed():
    query_document = parse('{ hello(name: """John""") }')
    assert (
        print_document(query_document)
        == dedent(
            """
        query {
          hello(name: \"\"\"John\"\"\")
        }
        """
        ).strip()
    )


def test_query_with_string_arg_with_quotes_is_printed():
    query_document = parse('{ hello(name: "John \\"doe\\"") }')
    assert (
        print_document(query_document)
        == dedent(
            """
        query {
          hello(name: \"John \\"doe\\"")
        }
        """
        ).strip()
    )


def test_query_with_fragments_is_printed():
    query_document = parse(
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
        print_document(query_document)
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


def test_all_queries_are_printed():
    query_document = parse(
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
        print_document(query_document)
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


def test_selected_query_is_printed():
    query_document = parse(
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
        print_document(query_document, operation_name="getCategory")
        == dedent(
            """
        query getCategory {
          category
        }
        """
        ).strip()
    )


def test_invalid_operation_error_is_raised_for_wrong_operation_name():
    query_document = parse(
        """
        query getUser {
            user
        }

        query getCategory {
            category
        }
        """
    )

    with pytest.raises(InvalidOperationNameError):
        print_document(query_document, operation_name="getProducts")
