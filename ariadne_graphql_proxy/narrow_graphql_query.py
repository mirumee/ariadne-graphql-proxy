from typing import Dict, List, Optional, Set, Tuple

from graphql import (
    InlineFragmentNode,
    FieldNode,
    FragmentSpreadNode,
    FragmentDefinitionNode,
    GraphQLResolveInfo,
    OperationDefinitionNode,
    SelectionNode,
    SelectionSetNode,
    VariableNode,
)


def narrow_graphql_query(
    info: GraphQLResolveInfo,
) -> Tuple[OperationDefinitionNode, Set[str]]:
    variables: List[str] = []

    # Remove ints from path
    clean_path = [
        path_item for path_item in info.path.as_list() if not isinstance(path_item, int)
    ]

    narrowed_selection_set = narrow_graphql_query_by_path(
        clean_path,
        info.operation.selection_set,
        info.fragments,
        variables,
    )

    variable_definitions = []
    for variable_node in info.operation.variable_definitions:
        if variable_node.variable.name.value in variables:
            variable_definitions.append(variable_node)

    operation = OperationDefinitionNode(
        name=info.operation.name,
        directives=info.operation.directives,
        variable_definitions=tuple(variable_definitions),
        selection_set=narrowed_selection_set,
        operation=info.operation.operation,
    )

    return operation, set(variables)


def narrow_graphql_query_by_path(
    path: List[str],
    selection_set: SelectionSetNode,
    fragments: Dict[str, FragmentDefinitionNode],
    variables: List[str],
) -> Optional[SelectionSetNode]:
    if not path:
        return get_graphql_query_subset(selection_set, fragments, variables)

    field_name = path[0]

    narrowed_inline_fragments = []

    for node in selection_set.selections:
        if isinstance(node, FieldNode):
            if node.alias:
                node_name = node.alias.value
            else:
                node_name = node.name.value

            if node_name == field_name:
                find_variables_used_by_node(node, variables)

                if node.selection_set:
                    node_selection = narrow_graphql_query_by_path(
                        path[1:],
                        node.selection_set,
                        fragments,
                        variables,
                    )
                else:
                    node_selection = None

                return SelectionSetNode(
                    selections=(
                        FieldNode(
                            alias=node.alias,
                            name=node.name,
                            arguments=node.arguments,
                            selection_set=node_selection,
                        ),
                    ),
                )

        if isinstance(node, InlineFragmentNode):
            fragment_selection = narrow_graphql_query_by_path(
                path,
                node.selection_set,
                fragments,
                variables,
            )

            if fragment_selection:
                narrowed_inline_fragments.append(
                    InlineFragmentNode(
                        type_condition=node.type_condition,
                        selection_set=fragment_selection,
                    ),
                )

        if isinstance(node, FragmentSpreadNode):
            fragment = fragments[node.name.value]
            fragment_selection = narrow_graphql_query_by_path(
                path,
                fragment.selection_set,
                fragments,
                variables,
            )

            if fragment_selection:
                return fragment_selection

    if narrowed_inline_fragments:
        return SelectionSetNode(
            selections=tuple(narrowed_inline_fragments),
        )

    return None


def get_graphql_query_subset(
    selection_set: SelectionSetNode,
    fragments: Dict[str, FragmentDefinitionNode],
    variables: List[str],
) -> SelectionSetNode:
    selections: List[SelectionNode] = []

    for node in selection_set.selections:
        if isinstance(node, FieldNode):
            find_variables_used_by_node(node, variables)

            if node.selection_set:
                node_selection_set = get_graphql_query_subset(
                    node.selection_set, fragments, variables
                )
            else:
                node_selection_set = None

            selections.append(
                FieldNode(
                    alias=node.alias,
                    name=node.name,
                    arguments=node.arguments,
                    selection_set=node_selection_set,
                ),
            )

        if isinstance(node, InlineFragmentNode):
            node_selection_set = get_graphql_query_subset(
                node.selection_set, fragments, variables
            )

            if node_selection_set:
                selections.append(
                    InlineFragmentNode(
                        type_condition=node.type_condition,
                        selection_set=node_selection_set,
                    ),
                )

        if isinstance(node, FragmentSpreadNode):
            fragment = fragments[node.name.value]
            selections.extend(
                get_graphql_query_subset(
                    fragment.selection_set, fragments, variables
                ).selections
            )

    return SelectionSetNode(selections=tuple(selections))


def find_variables_used_by_node(node: FieldNode, variables: List[str]):
    if node.arguments:
        for argument in node.arguments:
            if isinstance(argument.value, VariableNode):
                variables.append(argument.value.name.value)
