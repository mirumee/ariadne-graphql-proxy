from typing import Dict, List, Optional, Tuple, cast

from graphql import (
    DocumentNode,
    FieldNode,
    FragmentSpreadNode,
    FragmentDefinitionNode,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    OperationDefinitionNode,
    SelectionSetNode,
)
from httpx import AsyncClient

from .exceptions import InvalidOperationNameError, MissingOperationNameError
from .print_operation import print_document


def create_root_resolver(
    schema: GraphQLSchema,
    server_url: str,
    *,
    exclude: Optional[List[Tuple[str, str]]] = None,
    edges: Optional[List[Tuple[str, str, List[str]]]] = None,
):
    exclude_map: Dict[str, List[str]] = {}
    if exclude:
        for type_name, type_field in exclude:
            exclude_map.setdefault(type_name, []).append(type_field)

    async def proxy_root_resolver(
        context_value: dict,
        operation_name: Optional[str],
        variables: Optional[dict],
        document: DocumentNode,
    ):
        document = get_operation(operation_name, document)

        if document and exclude_map:
            document = remove_query_fields(schema, document, exclude_map)
        if document and edges:
            document = replace_query_edges(schema, document, edges)

        if not document:
            return None

        headers = {}
        if context_value.get("request"):
            authorization = context_value["request"].headers.get("authorization")
            if authorization:
                headers["Authorization"] = authorization

        async with AsyncClient() as client:
            r = await client.post(
                server_url,
                headers=headers,
                json={
                    "operationName": operation_name,
                    "query": print_document(document),
                    "variables": variables,
                },
            )

            data = r.json()

        return data["data"]

    return proxy_root_resolver


def get_operation(
    operation_name: Optional[str],
    document: DocumentNode,
) -> DocumentNode:
    definitions: List[DocumentNode] = []

    if operation_name:
        found_operation = False

        for definition_node in document.definitions:
            if isinstance(definition_node, OperationDefinitionNode):
                operation_node = cast(OperationDefinitionNode, definition_node)
                name = operation_node.name.value if operation_node.name else None
                if name == operation_name:
                    definitions.append(operation_node)
                    found_operation = True

            elif isinstance(definition_node, FragmentDefinitionNode):
                definitions.append(definition_node)

        if not found_operation:
            raise InvalidOperationNameError(operation_name)

        return DocumentNode(definitions=tuple(definitions))

    if len(document.definitions) > 1:
        operations = 0
        for definition_node in document.definitions:
            if isinstance(definition_node, OperationDefinitionNode):
                operations += 1

        if operations > 1:
            raise MissingOperationNameError()

    return document


def remove_query_fields(
    schema: GraphQLSchema,
    document: DocumentNode,
    exclude: Dict[str, List[str]],
) -> Optional[DocumentNode]:
    definitions = []
    has_operation = False
    for definition_node in document.definitions:
        if isinstance(definition_node, OperationDefinitionNode):
            operation_node = cast(OperationDefinitionNode, definition_node)
            new_operation = remove_query_fields_from_operation(
                schema, exclude, operation_node
            )
            if new_operation:
                definitions.append(new_operation)
                has_operation = True

        elif isinstance(definition_node, FragmentDefinitionNode):
            fragment_node = cast(FragmentDefinitionNode, definition_node)
            new_fragment = remove_query_fields_from_fragment(
                schema, exclude, fragment_node
            )
            if new_operation:
                definitions.append(new_fragment)

    if not has_operation:
        return None

    return DocumentNode(definitions=tuple(definitions))


def remove_query_fields_from_operation(
    schema: GraphQLSchema,
    exclude: Dict[str, List[str]],
    operation_node: OperationDefinitionNode,
) -> Optional[OperationDefinitionNode]:
    graphql_type = operation_node.operation.value.title()
    if graphql_type not in schema.type_map:
        return operation_node

    new_selection_set = remove_query_fields_from_selection_set(
        schema, graphql_type, exclude, operation_node.selection_set
    )

    if not new_selection_set:
        return None

    return OperationDefinitionNode(
        loc=operation_node.loc,
        operation=operation_node.operation,
        name=operation_node.name,
        directives=operation_node.directives,
        variable_definitions=operation_node.variable_definitions,
        selection_set=new_selection_set,
    )


def remove_query_fields_from_fragment(
    schema: GraphQLSchema,
    document: DocumentNode,
    exclude: Dict[str, List[str]],
    fragment_node: FragmentDefinitionNode,
) -> Optional[FragmentDefinitionNode]:
    return fragment_node


def remove_query_fields_from_selection_set(
    schema: GraphQLSchema,
    graphql_type_name,
    exclude: Dict[str, List[str]],
    selection_set: SelectionSetNode,
) -> Optional[SelectionSetNode]:
    exclude_fields = exclude.get(graphql_type_name)

    new_selections = []
    for selection in selection_set.selections:
        if isinstance(selection, FragmentSpreadNode):
            new_selections.append(selection)
            continue

        field_name = selection.name.value
        if exclude_fields and field_name in exclude_fields:
            continue  # Skip field because its explicitly excluded

        if not selection.selection_set:
            new_selections.append(selection)
            continue

        field_graphql_type = schema.type_map[graphql_type_name].fields[field_name].type

        # Unwrap wrapped type
        while isinstance(field_graphql_type, (GraphQLNonNull, GraphQLList)):
            field_graphql_type = field_graphql_type.of_type

        if isinstance(field_graphql_type, (GraphQLInterfaceType, GraphQLObjectType)):
            field_selection_set = remove_query_fields_from_selection_set(
                schema, field_graphql_type.name, exclude, selection.selection_set
            )
            if not field_selection_set:
                continue  # Skip field because its selection set was excluded

            new_selections.append(
                FieldNode(
                    loc=selection.loc,
                    directives=selection.directives,
                    alias=selection.alias,
                    name=selection.name,
                    arguments=selection.arguments,
                    selection_set=field_selection_set,
                )
            )

    if not new_selections:
        return None

    return SelectionSetNode(selections=new_selections)


def replace_query_edges(
    schema: GraphQLSchema,
    edges: List[Tuple[str, str, List[str]]],
    operation_name: Optional[str],
    document: DocumentNode,
) -> DocumentNode:
    return document
