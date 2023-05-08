from textwrap import dedent
from typing import Dict, List

from graphql import FragmentDefinitionNode, OperationDefinitionNode, parse

from ariadne_graphql_proxy import narrow_graphql_query, print_operation


class MockGraphQLResolveInfoPath:
    def __init__(self, path):
        self._path = path

    def as_list(self):
        return self._path


class MockGraphQLResolveInfo:
    path: MockGraphQLResolveInfoPath
    operation: OperationDefinitionNode
    fragments: Dict[str, FragmentDefinitionNode]

    def __init__(self, path: List[str], query: str):
        self.path = MockGraphQLResolveInfoPath(path)
        self.fragments = {}

        document = parse(query)
        for definition in document.definitions:
            if isinstance(definition, OperationDefinitionNode):
                self.operation = definition
            elif isinstance(definition, FragmentDefinitionNode):
                self.fragments[definition.name.value] = definition


def test_shallow_query_is_narrowed_to_top_level_field():
    narrowed_query, variables = narrow_graphql_query(
        MockGraphQLResolveInfo(
            ["field"],
            """
            { field }
            """,
        )
    )

    assert not variables
    assert (
        print_operation(narrowed_query)
        == dedent(
            """
        query {
          field
        }
        """
        ).strip()
    )


def test_single_top_field_query_is_narrowed_to_top_level_field_and_its_selection():
    narrowed_query, variables = narrow_graphql_query(
        MockGraphQLResolveInfo(
            ["field"],
            """
            { field { sub select { id other } } }
            """,
        )
    )

    assert not variables
    assert (
        print_operation(narrowed_query)
        == dedent(
            """
        query {
          field {
            sub
            select {
              id
              other
            }
          }
        }
        """
        ).strip()
    )


def test_multiple_top_fields_query_is_narrowed_to_top_level_field_and_its_selection():
    narrowed_query, variables = narrow_graphql_query(
        MockGraphQLResolveInfo(
            ["field"],
            """
            { field { sub select { id other } } exclude { me } }
            """,
        )
    )

    assert not variables
    assert (
        print_operation(narrowed_query)
        == dedent(
            """
        query {
          field {
            sub
            select {
              id
              other
            }
          }
        }
        """
        ).strip()
    )


def test_query_is_narrowed_using_deep_path():
    narrowed_query, variables = narrow_graphql_query(
        MockGraphQLResolveInfo(
            ["field", "select"],
            """
            { field { sub select { id other } other } exclude { me } }
            """,
        )
    )

    assert not variables
    assert (
        print_operation(narrowed_query)
        == dedent(
            """
        query {
          field {
            select {
              id
              other
            }
          }
        }
        """
        ).strip()
    )


def test_query_is_narrowed_using_two_levels_deep_path():
    narrowed_query, variables = narrow_graphql_query(
        MockGraphQLResolveInfo(
            ["field", "select"],
            """
            { field { sub select { id other } other } exclude { me } }
            """,
        )
    )

    assert not variables
    assert (
        print_operation(narrowed_query)
        == dedent(
            """
        query {
          field {
            select {
              id
              other
            }
          }
        }
        """
        ).strip()
    )


def test_query_is_narrowed_to_leaf_field_using_deep_path():
    narrowed_query, variables = narrow_graphql_query(
        MockGraphQLResolveInfo(
            ["field", "select", "other"],
            """
            { field { sub select { id other } other } exclude { me } }
            """,
        )
    )

    assert not variables
    assert (
        print_operation(narrowed_query)
        == dedent(
            """
        query {
          field {
            select {
              other
            }
          }
        }
        """
        ).strip()
    )


def test_unused_variables_are_stripped_from_narrowed_query():
    narrowed_query, variables = narrow_graphql_query(
        MockGraphQLResolveInfo(
            ["field", "select"],
            """
            query Test($var: ID!, $start: Int!) {
                field {
                    sub
                    select(start: $start) {
                        id
                        other(list: true)
                    }
                    other
                }
                exclude {
                    me(filter: $var)
                }
            }
            """,
        )
    )

    assert variables == set(["start"])
    assert (
        print_operation(narrowed_query)
        == dedent(
            """
        query Test($start: Int!) {
          field {
            select(start: $start) {
              id
              other(list: true)
            }
          }
        }
        """
        ).strip()
    )


def test_narrowed_query_traverses_fragments():
    narrowed_query, variables = narrow_graphql_query(
        MockGraphQLResolveInfo(
            ["field", "select"],
            """
            query Test($var: ID!, $start: Int!) {
              ...Data
              exclude {
                me(filter: $var)
              }
            }

            fragment Data on Field {
              field {
                sub
                select(start: $start) {
                  id
                  other(list: true) {
                    lorem
                    ipsum
                  }
                }
              }
            }
            """,
        )
    )

    assert variables == set(["start"])
    assert (
        print_operation(narrowed_query)
        == dedent(
            """
        query Test($start: Int!) {
          field {
            select(start: $start) {
              id
              other(list: true) {
                lorem
                ipsum
              }
            }
          }
        }
        """
        ).strip()
    )


def test_narrowed_query_inlines_fragments():
    narrowed_query, variables = narrow_graphql_query(
        MockGraphQLResolveInfo(
            ["field", "select"],
            """
            query Test($var: ID!, $start: Int!) {
                field {
                    sub
                    select(start: $start) {
                        ...Data
                    }
                    other
                }
                exclude {
                    me(filter: $var)
                }
            }

            fragment Data on Select {
              id
              other(list: true) {
                lorem
                ipsum
              }
            }
            """,
        )
    )

    assert variables == set(["start"])
    assert (
        print_operation(narrowed_query)
        == dedent(
            """
        query Test($start: Int!) {
          field {
            select(start: $start) {
              id
              other(list: true) {
                lorem
                ipsum
              }
            }
          }
        }
        """
        ).strip()
    )
