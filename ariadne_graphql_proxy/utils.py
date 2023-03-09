from typing import List, Optional, cast

from graphql import (
    DocumentNode,
    GraphQLError,
    OperationDefinitionNode,
)


def get_operation_by_name(
    document: DocumentNode,
    operation_name: Optional[str] = None,
) -> OperationDefinitionNode:
    operations: List[OperationDefinitionNode] = []
    for definition in document.definitions:
        if isinstance(definition, OperationDefinitionNode):
            operations.append(definition)

    if not operations:
        raise GraphQLError(f"Query document did not contain any operations.")

    if len(operations) == 1:
        operation = cast(OperationDefinitionNode, operations[0])

        if not operation_name:
            return operation

        if not operation.name or operation.name.value != operation_name:
            raise GraphQLError(
                f"Query document did not contain an " f"operation '{operation_name}'."
            )

        return operation
