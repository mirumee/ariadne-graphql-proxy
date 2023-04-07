from textwrap import dedent

from graphql import parse

from ariadne_graphql_proxy import print_fragment


def test_fragment_is_printed():
    fragment_node = parse(
        """
        fragment UserData on User {
            id
            email
        }
        """
    ).definitions[0]
    assert (
        print_fragment(fragment_node)
        == dedent(
            """
        fragment UserData on User {
          id
          email
        }
        """
        ).strip()
    )


def test_fragment_with_subfields_is_printed():
    fragment_node = parse(
        """
        fragment UserData on User {
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
    ).definitions[0]
    assert (
        print_fragment(fragment_node)
        == dedent(
            """
        fragment UserData on User {
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


def test_fragment_with_alias_field_is_printed():
    fragment_node = parse(
        """
        fragment UserData on User {
            greeting: hello
        }
        """
    ).definitions[0]
    assert (
        print_fragment(fragment_node)
        == dedent(
            """
        fragment UserData on User {
          greeting: hello
        }
        """
        ).strip()
    )
