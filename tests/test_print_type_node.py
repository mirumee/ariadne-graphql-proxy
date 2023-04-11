from graphql import parse

from ariadne_graphql_proxy import print_type_node


def parse_for_field_node(text: str):
    return parse(text).definitions[0].variable_definitions[0].type


def test_named_type_node_is_printed():
    type_node = parse_for_field_node(
        """
        query Test($var: String) {
            field(arg: $var)
        }
        """
    )
    assert print_type_node(type_node) == "String"


def test_non_nullable_type_node_is_printed():
    type_node = parse_for_field_node(
        """
        query Test($var: String!) {
            field(arg: $var)
        }
        """
    )
    assert print_type_node(type_node) == "String!"


def test_list_type_node_is_printed():
    type_node = parse_for_field_node(
        """
        query Test($var: [String]) {
            field(arg: $var)
        }
        """
    )
    assert print_type_node(type_node) == "[String]"


def test_non_nullable_list_type_node_is_printed():
    type_node = parse_for_field_node(
        """
        query Test($var: [String]!) {
            field(arg: $var)
        }
        """
    )
    assert print_type_node(type_node) == "[String]!"


def test_non_nullable_list_type_node_with_non_nullable_value_is_printed():
    type_node = parse_for_field_node(
        """
        query Test($var: [String!]!) {
            field(arg: $var)
        }
        """
    )
    assert print_type_node(type_node) == "[String!]!"
