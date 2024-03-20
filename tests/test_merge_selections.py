from textwrap import dedent

from graphql import SelectionSetNode, parse, print_ast

from ariadne_graphql_proxy import merge_selections


def test_merge_selections_merges_two_flat_sets():
    set_a = parse("{ hello }").definitions[0].selection_set.selections
    set_b = parse("{ world }").definitions[0].selection_set.selections

    result = merge_selections(set_a, set_b)
    assert (
        print_ast(SelectionSetNode(selections=result))
        == dedent(
            """
        {
          hello
          world
        }
        """
        ).strip()
    )


def test_merge_selections_merges_two_overlapping_flat_sets():
    set_a = parse("{ hello world }").definitions[0].selection_set.selections
    set_b = parse("{ world }").definitions[0].selection_set.selections

    result = merge_selections(set_a, set_b)
    assert (
        print_ast(SelectionSetNode(selections=result))
        == dedent(
            """
        {
          hello
          world
        }
        """
        ).strip()
    )


def test_merge_selections_keeps_nested_selections():
    set_a = parse("{ hello { sub } }").definitions[0].selection_set.selections
    set_b = parse("{ world }").definitions[0].selection_set.selections

    result = merge_selections(set_a, set_b)
    assert (
        print_ast(SelectionSetNode(selections=result))
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


def test_merge_selections_merges_selection_sets_recursively():
    set_a = parse("{ hello { sub } }").definitions[0].selection_set.selections
    set_b = parse("{ hello { set } world }").definitions[0].selection_set.selections

    result = merge_selections(set_a, set_b)
    assert (
        print_ast(SelectionSetNode(selections=result))
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
