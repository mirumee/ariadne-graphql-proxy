from textwrap import dedent

from graphql import parse, print_ast

from ariadne_graphql_proxy import merge_selection_sets


def test_merge_selection_sets_merges_two_flat_sets():
    set_a = parse("{ hello }").definitions[0].selection_set
    set_b = parse("{ world }").definitions[0].selection_set

    result = merge_selection_sets(set_a, set_b)
    assert (
        print_ast(result)
        == dedent(
            """
        {
          hello
          world
        }
        """
        ).strip()
    )


def test_merge_selection_sets_merges_two_overlapping_flat_sets():
    set_a = parse("{ hello world }").definitions[0].selection_set
    set_b = parse("{ world }").definitions[0].selection_set

    result = merge_selection_sets(set_a, set_b)
    assert (
        print_ast(result)
        == dedent(
            """
        {
          hello
          world
        }
        """
        ).strip()
    )


def test_merge_selection_sets_keeps_nested_selections():
    set_a = parse("{ hello { sub } }").definitions[0].selection_set
    set_b = parse("{ world }").definitions[0].selection_set

    result = merge_selection_sets(set_a, set_b)
    assert (
        print_ast(result)
        == dedent(
            """
        {
          hello {
            sub
          }
          world
        }
        """
        ).strip()
    )


def test_merge_selection_sets_merges_selection_sets_recursively():
    set_a = parse("{ hello { sub } }").definitions[0].selection_set
    set_b = parse("{ hello { set } world }").definitions[0].selection_set

    result = merge_selection_sets(set_a, set_b)
    assert (
        print_ast(result)
        == dedent(
            """
        {
          hello {
            sub
            set
          }
          world
        }
        """
        ).strip()
    )
