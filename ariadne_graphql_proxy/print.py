import textwrap
from typing import Optional, cast

from graphql import (
    BooleanValueNode,
    ConstListValueNode,
    ConstObjectValueNode,
    DocumentNode,
    EnumValueNode,
    FieldNode,
    FloatValueNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLResolveInfo,
    IntValueNode,
    ListTypeNode,
    ListValueNode,
    NamedTypeNode,
    NonNullTypeNode,
    NullValueNode,
    ObjectValueNode,
    OperationDefinitionNode,
    SelectionSetNode,
    StringValueNode,
    TypeNode,
    ValueNode,
    VariableNode,
)

from .get_operation import get_operation


def print_document(
    document_node: DocumentNode,
    *,
    operation_name: Optional[str] = None,
    indent: int = 2,
) -> str:
    if operation_name:
        return print_named_operation(
            document_node,
            operation_name,
            indent=indent,
        )

    return print_all_operations(document_node, indent=indent)


def print_named_operation(
    document_node: DocumentNode,
    operation_name: str,
    *,
    indent: int = 2,
) -> str:
    operation_node = get_operation(document_node, operation_name)
    return print_operation(operation_node, indent=indent)


def print_all_operations(
    document_node: DocumentNode,
    *,
    indent: int = 2,
) -> str:
    operations = []

    for definition_node in document_node.definitions:
        if isinstance(definition_node, OperationDefinitionNode):
            operation_node = cast(OperationDefinitionNode, definition_node)
            operations.append(print_operation(operation_node, indent=indent))
        elif isinstance(definition_node, FragmentDefinitionNode):
            fragment_node = cast(FragmentDefinitionNode, definition_node)
            operations.append(print_fragment(fragment_node, indent=indent))

    return "\n\n".join(operations)


def print_operation(operation_node: OperationDefinitionNode, *, indent: int = 2) -> str:
    operation_header = print_operation_header(operation_node)
    selection_set = print_selection_set(operation_node.selection_set, indent=indent)

    return f"{operation_header} {'{'}\n{selection_set}\n{'}'}"


def print_operation_header(operation_node: OperationDefinitionNode) -> str:
    operation = operation_node.operation.value
    name = operation_node.name.value if operation_node.name else None

    if name:
        query_header = f"{operation} {name}"
    else:
        query_header = operation

    if operation_node.variable_definitions:
        variables = print_operation_variables(operation_node)
        query_header = f"{query_header}({variables})"

    if operation_node.directives:
        raise NotImplementedError("TODO: operation directives are not implemented yet")

    return query_header


def print_operation_variables(operation_node: OperationDefinitionNode) -> str:
    variables = []
    for variable_node in operation_node.variable_definitions:
        name = f"${variable_node.variable.name.value}"
        type_ = print_type_node(variable_node.type)

        variable_str = f"{name}: {type_}"
        if variable_node.default_value:
            variable_str += f" = {print_value(variable_node.default_value)}"

        variables.append(variable_str)

    return ", ".join(variables)


def print_type_node(type_node: TypeNode) -> str:
    if isinstance(type_node, NamedTypeNode):
        return type_node.name.value

    if isinstance(type_node, NonNullTypeNode):
        return f"{print_type_node(type_node.type)}!"

    if isinstance(type_node, ListTypeNode):
        return f"[{print_type_node(type_node.type)}]"

    raise ValueError(f"Unknown type node: {repr(type_node)}")


def print_fragment(fragment_node: FragmentDefinitionNode, *, indent: int = 2) -> str:
    name = fragment_node.name.value
    on_type = fragment_node.type_condition.name.value
    selection_set = print_selection_set(fragment_node.selection_set, indent=indent)

    fragment_header = f"fragment {name} on {on_type}"
    return f"{fragment_header} {'{'}\n{selection_set}\n{'}'}"


def print_selection_set(selection_set: SelectionSetNode, *, indent: int = 2) -> str:
    selections = []

    for selection in selection_set.selections:
        if isinstance(selection, FieldNode):
            selections.append(print_field(selection, indent=indent))
        elif isinstance(selection, FragmentSpreadNode):
            fragment_name = selection.name.value
            selections.append(f"...{fragment_name}")
        else:
            raise ValueError(f"Unknown node: {repr(selection)}")

    return textwrap.indent("\n".join(selections), " " * indent)


def print_field(field_node: FieldNode, *, indent: int = 2) -> str:
    alias = field_node.alias.value if field_node.alias else None
    name = field_node.name.value

    field_str = f"{alias}: {name}" if alias else name

    if field_node.arguments:
        field_str += f"({print_field_arguments(field_node)})"

    if field_node.selection_set:
        field_str += f" {'{'}\n{print_selection_set(field_node.selection_set)}\n{'}'}"

    return field_str


def print_field_arguments(field_node: FieldNode):
    arguments = []

    for argument in field_node.arguments:
        name = argument.name.value
        value = print_value(argument.value)
        arguments.append(f"{name}: {value}")

    return ", ".join(arguments)


def print_value(value_node: ValueNode) -> str:
    if isinstance(value_node, VariableNode):
        return f"${value_node.name.value}"

    if isinstance(value_node, BooleanValueNode):
        return "true" if value_node.value else "false"

    if isinstance(value_node, (IntValueNode, FloatValueNode)):
        return value_node.value

    if isinstance(value_node, (IntValueNode, FloatValueNode, EnumValueNode)):
        return value_node.value

    if isinstance(value_node, NullValueNode):
        return "null"

    if isinstance(value_node, StringValueNode):
        escaped_str = value_node.value.replace('"', '\\"')
        if value_node.block:
            return f'"""{escaped_str}"""'
        return f'"{escaped_str}"'

    if isinstance(value_node, (ListValueNode, ConstListValueNode)):
        items = ", ".join(print_value(item_value) for item_value in value_node.values)
        return f"[{items}]"

    if isinstance(value_node, (ObjectValueNode, ConstObjectValueNode)):
        fields = []
        for field in value_node.fields:
            field_name = field.name.value
            field_value = print_value(field.value)
            fields.append(f"{field_name}: {field_value}")

        return f"{'{'} {', '.join(fields)} {'}'}"

    raise ValueError(f"Unknown value node: {repr(value_node)}")
