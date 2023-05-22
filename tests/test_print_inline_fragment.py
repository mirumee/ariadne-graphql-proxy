from textwrap import dedent

from graphql import parse

from ariadne_graphql_proxy import print_inline_fragment


def parse_for_inline_fragment(text: str):
    field_definition = parse(text).definitions[0].selection_set.selections[0]
    return field_definition.selection_set.selections[0]


def test_inline_fragment_is_printed():
    inline_fragment = parse_for_inline_fragment(
        """
        query GetHello {
            results {
                ... on User {
                    username
                    email
                }
            }
        }
        """
    )

    assert (
        print_inline_fragment(inline_fragment)
        == dedent(
            """
        ... on User {
          username
          email
        }
        """
        ).strip()
    )


def test_inline_fragment_with_sub_selections_is_printed():
    inline_fragment = parse_for_inline_fragment(
        """
        query GetHello {
            results {
                ... on User {
                    username
                    email
                    group {
                        id
                        name
                    }
                }
            }
        }
        """
    )

    assert (
        print_inline_fragment(inline_fragment)
        == dedent(
            """
        ... on User {
          username
          email
          group {
            id
            name
          }
        }
        """
        ).strip()
    )
