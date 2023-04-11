from graphql import parse

from ariadne_graphql_proxy import print_field


def parse_for_field_node(text: str):
    return parse(text).definitions[0].selection_set.selections[0]


def test_field_is_printed():
    field_node = parse_for_field_node("{ field }")
    assert print_field(field_node) == "field"


def test_aliased_field_is_printed():
    field_node = parse_for_field_node("{ alias: field }")
    assert print_field(field_node) == "alias: field"


def test_field_with_single_argument_is_printed():
    field_node = parse_for_field_node("{ field(arg: ADMIN) }")
    assert print_field(field_node) == "field(arg: ADMIN)"


def test_field_with_multiple_arguments_is_printed():
    field_node = parse_for_field_node("{ field(arg: ADMIN, other: 2) }")
    assert print_field(field_node) == "field(arg: ADMIN, other: 2)"
