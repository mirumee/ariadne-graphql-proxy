from textwrap import dedent

from graphql import parse

from ariadne_graphql_proxy import print_operation


def test_anonymous_operation_is_printed():
    operation_node = parse("{ hello }").definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query {
          hello
        }
        """
        ).strip()
    )


def test_named_operation_is_printed():
    operation_node = parse("query GetHello { hello }").definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello {
          hello
        }
        """
        ).strip()
    )


def test_anonymous_mutation_operation_is_printed():
    operation_node = parse("mutation { hello }").definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        mutation {
          hello
        }
        """
        ).strip()
    )


def test_named_mutation_operation_is_printed():
    operation_node = parse("mutation SetHello { hello }").definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        mutation SetHello {
          hello
        }
        """
        ).strip()
    )


def test_named_operation_with_optional_string_argument_is_printed():
    operation_node = parse(
        """
        query GetHello($value: String) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello($value: String) {
          hello(arg: $value)
        }
        """
        ).strip()
    )


def test_named_operation_with_required_string_argument_is_printed():
    operation_node = parse(
        """
        query GetHello($value: String!) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello($value: String!) {
          hello(arg: $value)
        }
        """
        ).strip()
    )


def test_named_operation_with_string_argument_with_default_value_is_printed():
    operation_node = parse(
        """
        query GetHello($value: String = "default") {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello($value: String = "default") {
          hello(arg: $value)
        }
        """
        ).strip()
    )


def test_named_operation_with_optional_integer_argument_is_printed():
    operation_node = parse(
        """
        query GetHello($value: Int) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello($value: Int) {
          hello(arg: $value)
        }
        """
        ).strip()
    )


def test_named_operation_with_required_integer_argument_is_printed():
    operation_node = parse(
        """
        query GetHello($value: Int!) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello($value: Int!) {
          hello(arg: $value)
        }
        """
        ).strip()
    )


def test_named_operation_with_integer_argument_with_default_value_is_printed():
    operation_node = parse(
        """
        query GetHello($value: Int = 42) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello($value: Int = 42) {
          hello(arg: $value)
        }
        """
        ).strip()
    )


def test_named_operation_with_optional_float_argument_is_printed():
    operation_node = parse(
        """
        query GetHello($value: Float) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello($value: Float) {
          hello(arg: $value)
        }
        """
        ).strip()
    )


def test_named_operation_with_required_float_argument_is_printed():
    operation_node = parse(
        """
        query GetHello($value: Float!) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello($value: Float!) {
          hello(arg: $value)
        }
        """
        ).strip()
    )


def test_named_operation_with_float_argument_with_default_value_is_printed():
    operation_node = parse(
        """
        query GetHello($value: Float = 4.2) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello($value: Float = 4.2) {
          hello(arg: $value)
        }
        """
        ).strip()
    )


def test_named_operation_with_optional_boolean_argument_is_printed():
    operation_node = parse(
        """
        query GetHello($value: Boolean) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello($value: Boolean) {
          hello(arg: $value)
        }
        """
        ).strip()
    )


def test_named_operation_with_required_boolean_argument_is_printed():
    operation_node = parse(
        """
        query GetHello($value: Boolean!) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello($value: Boolean!) {
          hello(arg: $value)
        }
        """
        ).strip()
    )


def test_named_operation_with_boolean_argument_with_default_true_is_printed():
    operation_node = parse(
        """
        query GetHello($value: Boolean = true) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello($value: Boolean = true) {
          hello(arg: $value)
        }
        """
        ).strip()
    )


def test_named_operation_with_boolean_argument_with_default_false_is_printed():
    operation_node = parse(
        """
        query GetHello($value: Boolean = false) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello($value: Boolean = false) {
          hello(arg: $value)
        }
        """
        ).strip()
    )


def test_named_operation_with_optional_input_argument_is_printed():
    operation_node = parse(
        """
        query GetHello($value: MyInput) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello($value: MyInput) {
          hello(arg: $value)
        }
        """
        ).strip()
    )


def test_named_operation_with_required_input_argument_is_printed():
    operation_node = parse(
        """
        query GetHello($value: MyInput!) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello($value: MyInput!) {
          hello(arg: $value)
        }
        """
        ).strip()
    )


def test_named_operation_with_input_argument_with_default_value_is_printed():
    operation_node = parse(
        """
        query GetHello($value: MyInput = { name: "bob" }) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello($value: MyInput = { name: "bob" }) {
          hello(arg: $value)
        }
        """
        ).strip()
    )


def test_named_operation_with_optional_list_argument_is_printed():
    operation_node = parse(
        """
        query GetHello($value: [MyInput]) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello($value: [MyInput]) {
          hello(arg: $value)
        }
        """
        ).strip()
    )


def test_named_operation_with_required_list_argument_is_printed():
    operation_node = parse(
        """
        query GetHello($value: [MyInput]!) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello($value: [MyInput]!) {
          hello(arg: $value)
        }
        """
        ).strip()
    )


def test_named_operation_with_required_non_nullable_list_argument_is_printed():
    operation_node = parse(
        """
        query GetHello($value: [MyInput!]!) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello($value: [MyInput!]!) {
          hello(arg: $value)
        }
        """
        ).strip()
    )


def test_named_operation_with_nested_fields_is_printed():
    operation_node = parse(
        """
        query GetUser {
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
        print_operation(operation_node)
        == dedent(
            """
        query GetUser {
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


def test_named_operation_with_alias_field_is_printed():
    operation_node = parse(
        """
        query GetHello {
            greeting: hello
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello {
          greeting: hello
        }
        """
        ).strip()
    )


def test_named_operation_with_fragment_is_printed():
    operation_node = parse(
        """
        query GetHello {
            ...UserData
        }
        """
    ).definitions[0]
    assert (
        print_operation(operation_node)
        == dedent(
            """
        query GetHello {
          ...UserData
        }
        """
        ).strip()
    )
