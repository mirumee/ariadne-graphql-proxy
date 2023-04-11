from graphql import parse

from ariadne_graphql_proxy import print_field_arguments


def parse_for_field_node(text: str):
    return parse(text).definitions[0].selection_set.selections[0]


def test_single_argument_with_variable_value_is_printed():
    field_node = parse_for_field_node("{ field(arg: $var) }")
    assert print_field_arguments(field_node) == "arg: $var"


def test_single_argument_with_string_literal_value_is_printed():
    field_node = parse_for_field_node('{ field(arg: "test") }')
    assert print_field_arguments(field_node) == 'arg: "test"'


def test_single_argument_with_int_literal_value_is_printed():
    field_node = parse_for_field_node("{ field(arg: 12) }")
    assert print_field_arguments(field_node) == "arg: 12"


def test_single_argument_with_false_literal_value_is_printed():
    field_node = parse_for_field_node("{ field(arg: false) }")
    assert print_field_arguments(field_node) == "arg: false"


def test_single_argument_with_true_literal_value_is_printed():
    field_node = parse_for_field_node("{ field(arg: true) }")
    assert print_field_arguments(field_node) == "arg: true"


def test_single_argument_with_null_literal_value_is_printed():
    field_node = parse_for_field_node("{ field(arg: null) }")
    assert print_field_arguments(field_node) == "arg: null"


def test_single_argument_with_enum_literal_value_is_printed():
    field_node = parse_for_field_node("{ field(arg: ADMIN) }")
    assert print_field_arguments(field_node) == "arg: ADMIN"


def test_single_argument_with_list_literal_value_is_printed():
    field_node = parse_for_field_node("{ field(arg: [1, 3]) }")
    assert print_field_arguments(field_node) == "arg: [1, 3]"


def test_single_argument_with_object_literal_value_is_printed():
    field_node = parse_for_field_node('{ field(arg: {key: 1, name: "test"}) }')
    assert print_field_arguments(field_node) == 'arg: { key: 1, name: "test" }'


def test_multiple_arguments_are_printed():
    field_node = parse_for_field_node("{ field(arg: $var, other: TEST) }")
    assert print_field_arguments(field_node) == "arg: $var, other: TEST"
