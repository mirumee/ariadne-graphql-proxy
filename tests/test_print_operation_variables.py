from graphql import parse

from ariadne_graphql_proxy import print_operation_variables


def test_named_operation_variables_with_optional_string_argument_are_printed():
    operation_node = parse(
        """
        query GetHello($value: String) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert print_operation_variables(operation_node) == "$value: String"


def test_named_operation_variables_with_required_string_argument_are_printed():
    operation_node = parse(
        """
        query GetHello($value: String!) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert print_operation_variables(operation_node) == "$value: String!"


def test_named_operation_variables_with_string_argument_with_default_value_are_printed():
    operation_node = parse(
        """
        query GetHello($value: String = "default") {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert print_operation_variables(operation_node) == '$value: String = "default"'


def test_named_operation_variables_with_optional_integer_argument_are_printed():
    operation_node = parse(
        """
        query GetHello($value: Int) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert print_operation_variables(operation_node) == "$value: Int"


def test_named_operation_variables_with_required_integer_argument_are_printed():
    operation_node = parse(
        """
        query GetHello($value: Int!) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert print_operation_variables(operation_node) == "$value: Int!"


def test_named_operation_variables_with_integer_argument_with_default_value_are_printed():
    operation_node = parse(
        """
        query GetHello($value: Int = 42) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert print_operation_variables(operation_node) == "$value: Int = 42"


def test_named_operation_variables_with_optional_float_argument_are_printed():
    operation_node = parse(
        """
        query GetHello($value: Float) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert print_operation_variables(operation_node) == "$value: Float"


def test_named_operation_variables_with_required_float_argument_are_printed():
    operation_node = parse(
        """
        query GetHello($value: Float!) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert print_operation_variables(operation_node) == "$value: Float!"


def test_named_operation_variables_with_float_argument_with_default_value_are_printed():
    operation_node = parse(
        """
        query GetHello($value: Float = 4.2) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert print_operation_variables(operation_node) == "$value: Float = 4.2"


def test_named_operation_variables_with_optional_boolean_argument_are_printed():
    operation_node = parse(
        """
        query GetHello($value: Boolean) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert print_operation_variables(operation_node) == "$value: Boolean"


def test_named_operation_variables_with_required_boolean_argument_are_printed():
    operation_node = parse(
        """
        query GetHello($value: Boolean!) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert print_operation_variables(operation_node) == "$value: Boolean!"


def test_named_operation_variables_with_boolean_argument_with_default_true_are_printed():
    operation_node = parse(
        """
        query GetHello($value: Boolean = true) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert print_operation_variables(operation_node) == "$value: Boolean = true"


def test_named_operation_variables_with_boolean_argument_with_default_false_are_printed():
    operation_node = parse(
        """
        query GetHello($value: Boolean = false) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert print_operation_variables(operation_node) == "$value: Boolean = false"


def test_named_operation_variables_with_optional_input_argument_are_printed():
    operation_node = parse(
        """
        query GetHello($value: MyInput) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert print_operation_variables(operation_node) == "$value: MyInput"


def test_named_operation_variables_with_required_input_argument_are_printed():
    operation_node = parse(
        """
        query GetHello($value: MyInput!) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert print_operation_variables(operation_node) == "$value: MyInput!"


def test_named_operation_variables_with_input_argument_with_default_value_are_printed():
    operation_node = parse(
        """
        query GetHello($value: MyInput = {name: "bob"}) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert (
        print_operation_variables(operation_node) == '$value: MyInput = { name: "bob" }'
    )


def test_named_operation_variables_with_optional_list_argument_are_printed():
    operation_node = parse(
        """
        query GetHello($value: [MyInput]) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert print_operation_variables(operation_node) == "$value: [MyInput]"


def test_named_operation_variables_with_required_list_argument_are_printed():
    operation_node = parse(
        """
        query GetHello($value: [MyInput]!) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert print_operation_variables(operation_node) == "$value: [MyInput]!"


def test_named_operation_variables_with_required_non_nullable_list_argument_are_printed():
    operation_node = parse(
        """
        query GetHello($value: [MyInput!]!) {
            hello(arg: $value)
        }
        """
    ).definitions[0]
    assert print_operation_variables(operation_node) == "$value: [MyInput!]!"
