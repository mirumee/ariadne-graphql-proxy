from typing import List, Optional

from graphql import (
    DocumentNode,
    GraphQLError,
    OperationDefinitionNode,
)


def get_operation(
    document: DocumentNode,
    operation_name: Optional[str] = None,
) -> OperationDefinitionNode:
    operations: List[OperationDefinitionNode] = []
    anonymous_operations = 0

    for definition in document.definitions:
        if isinstance(definition, OperationDefinitionNode):
            operations.append(definition)
            if not definition.name:
                anonymous_operations += 1

    if not operations:
        raise GraphQLError("Query did not contain any operations.")

    if len(operations) == 1:
        operation = operations[0]

        if not operation_name:
            return operation

        if not operation.name or operation.name.value != operation_name:
            raise UnknownOperationGraphQLError(operation_name)

        return operation

    if anonymous_operations == 1:
        raise GraphQLError("Query can't define both anonymous and named operations.")

    if anonymous_operations > 1:
        raise GraphQLError("Query can't define multiple anonymous operations.")

    if not operation_name:
        raise GraphQLError(
            "Operation name is required if query contains multiple operations."
        )

    for operation in operations:
        if operation.name and operation.name.value == operation_name:
            return operation

    raise UnknownOperationGraphQLError(operation_name)


class UnknownOperationGraphQLError(GraphQLError):
    def __init__(self, operation_name: str):
        super().__init__(f"Unknown operation named '{operation_name}'.")
