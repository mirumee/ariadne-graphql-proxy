from textwrap import dedent

from graphql import parse

from ariadne_graphql_proxy import print_selection_set


def test_simple_selection_set_is_printed():
    selection_set = parse("{ hello }").definitions[0].selection_set
    assert print_selection_set(selection_set) == "  hello"


def test_selection_set_with_nested_fields_is_printed():
    selection_set = (
        parse(
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
        .definitions[0]
        .selection_set
    )
    assert (
        print_selection_set(selection_set)
        == dedent(
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
        .strip()
        .strip("{}\n")
    )


def test_selection_set_with_alias_field_is_printed():
    selection_set = parse("query { greeting: hello }").definitions[0].selection_set
    assert print_selection_set(selection_set) == "  greeting: hello"


def test_selection_set_with_single_argument_is_printed():
    selection_set = (
        parse(
            """
        query GetHello($name: String!) {
            hello(name: $name)
        }
        """
        )
        .definitions[0]
        .selection_set
    )
    assert print_selection_set(selection_set) == "  hello(name: $name)"


def test_selection_set_with_multiple_arguments_is_printed():
    selection_set = (
        parse(
            """
        query GetHello($name: String!, $age: Int!) {
            hello(name: $name, age: $age)
        }
        """
        )
        .definitions[0]
        .selection_set
    )
    assert print_selection_set(selection_set) == "  hello(name: $name, age: $age)"


def test_selection_set_with_multiple_fields_and_arguments_is_printed():
    selection_set = (
        parse(
            """
        query GetHello($name: String!) {
            hello(name: $name, age: 21, birthplace: null)
        }
        """
        )
        .definitions[0]
        .selection_set
    )
    assert (
        print_selection_set(selection_set)
        == "  hello(name: $name, age: 21, birthplace: null)"
    )


def test_selection_set_with_variable_argument_is_printed():
    selection_set = parse("{ hello(name: $variable) }").definitions[0].selection_set
    assert print_selection_set(selection_set) == "  hello(name: $variable)"


def test_selection_set_with_list_argument_is_printed():
    selection_set = parse("{ hello(names: [1, 2, 3, 4]) }").definitions[0].selection_set
    assert print_selection_set(selection_set) == "  hello(names: [1, 2, 3, 4])"


def test_selection_set_with_null_argument_is_printed():
    selection_set = parse("{ hello(name: null) }").definitions[0].selection_set
    assert print_selection_set(selection_set) == "  hello(name: null)"


def test_selection_set_with_enum_argument_is_printed():
    selection_set = parse("{ hello(name: ADMIN) }").definitions[0].selection_set
    assert print_selection_set(selection_set) == "  hello(name: ADMIN)"


def test_selection_set_with_bool_true_argument_is_printed():
    selection_set = parse("{ hello(name: true) }").definitions[0].selection_set
    assert print_selection_set(selection_set) == "  hello(name: true)"


def test_selection_set_with_bool_false_argument_is_printed():
    selection_set = parse("{ hello(name: false) }").definitions[0].selection_set
    assert print_selection_set(selection_set) == "  hello(name: false)"


def test_selection_set_with_object_argument_is_printed():
    selection_set = (
        parse("{ hello(name: { from: 12, to: true }) }").definitions[0].selection_set
    )
    assert print_selection_set(selection_set) == "  hello(name: { from: 12, to: true })"


def test_selection_set_with_string_argument_is_printed():
    selection_set = parse('{ hello(name: "John") }').definitions[0].selection_set
    assert print_selection_set(selection_set) == '  hello(name: "John")'


def test_selection_set_with_block_string_argument_is_printed():
    selection_set = parse('{ hello(name: """John""") }').definitions[0].selection_set
    assert print_selection_set(selection_set) == '  hello(name: """John""")'


def test_selection_set_with_string_argument_containing_quotes_is_printed():
    selection_set = (
        parse('{ hello(name: "John \\"doe\\"") }').definitions[0].selection_set
    )
    assert print_selection_set(selection_set) == '  hello(name: "John \\"doe\\"")'


def test_selection_set_with_fragment_is_printed():
    selection_set = (
        parse(
            """
        query GetHello {
            ...UserData
        }
        """
        )
        .definitions[0]
        .selection_set
    )
    assert print_selection_set(selection_set) == "  ...UserData"
