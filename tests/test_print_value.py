from graphql import parse

from ariadne_graphql_proxy import print_value


def parse_for_value(text: str):
    return parse(text).definitions[0].selection_set.selections[0].arguments[0].value


def test_variable_value_is_printed():
    value_node = parse_for_value("{ hello(name: $variable) }")
    assert print_value(value_node) == "$variable"


def test_list_value_is_printed():
    value_node = parse_for_value("{ hello(names: [1, 2, 3, 4]) }")
    assert print_value(value_node) == "[1, 2, 3, 4]"


def test_null_value_is_printed():
    value_node = parse_for_value("{ hello(name: null) }")
    assert print_value(value_node) == "null"


def test_enum_value_is_printed():
    value_node = parse_for_value("{ hello(name: ADMIN) }")
    assert print_value(value_node) == "ADMIN"


def test_true_value_is_printed():
    value_node = parse_for_value("{ hello(name: true) }")
    assert print_value(value_node) == "true"


def test_false_value_is_printed():
    value_node = parse_for_value("{ hello(name: false) }")
    assert print_value(value_node) == "false"


def test_object_value_is_printed():
    value_node = parse_for_value("{ hello(name: { from: 12, to: true }) }")
    assert print_value(value_node) == "{ from: 12, to: true }"


def test_string_value_is_printed():
    value_node = parse_for_value('{ hello(name: "John") }')
    assert print_value(value_node) == '"John"'


def test_string_block_value_is_printed():
    value_node = parse_for_value('{ hello(name: """John""") }')
    assert print_value(value_node) == '"""John"""'


def test_string_value_containing_quotes_is_printed():
    value_node = parse_for_value('{ hello(name: "John \\"doe\\"") }')
    assert print_value(value_node) == '"John \\"doe\\""'
