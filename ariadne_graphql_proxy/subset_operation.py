from graphql import (
    DocumentNode,
    FragmentDefinitionNode,
    OperationDefinitionNode,
    SelectionSetNode,
)

from .print_operation import print_document
from .utils import get_operation_by_name


def subset_operation(info) -> dict:
    root_query = info.context["root_query"]
    root_operation = get_operation_by_name(
        root_query["document"], root_query["operationName"]
    )

    definitions = [
        OperationDefinitionNode(
            loc=root_operation.loc,
            operation=root_operation.operation,
            name=root_operation.name,
            directives=root_operation.directives,
            variable_definitions=root_operation.variable_definitions,
            selection_set=SelectionSetNode(
                selections=tuple(info.field_nodes),
            ),
        )
    ]

    for definition in root_query["document"].definitions:
        if isinstance(definition, FragmentDefinitionNode):
            definitions.append(definition)

    return {
        "operationName": root_query["operationName"],
        "query": print_document(DocumentNode(definitions=tuple(definitions))),
        "variables": root_query["variables"],
    }
