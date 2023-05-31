from typing import Any, Callable, Dict, List, Optional, Union, cast

from graphql import (
    DocumentNode,
    FieldNode,
    FragmentSpreadNode,
    GraphQLResolveInfo,
    NameNode,
    OperationDefinitionNode,
    SelectionNode,
    SelectionSetNode,
    parse,
    print_ast,
)

from .proxy_resolver import ProxyResolver
from .cache import CacheBackend


FIELDS_PLACEHOLDER = "__FIELDS"


class ForeignKeyResolver(ProxyResolver):
    _template: OperationDefinitionNode
    _operation_name: str
    _path: List[str]
    _variables: Optional[Dict[str, str]]

    def __init__(
        self,
        url: str,
        template: str,
        variables: Optional[Dict[str, str]] = None,
        proxy_headers: Union[bool, Callable, List[str]] = True,
        cache: Optional[CacheBackend] = None,
        cache_key: Optional[Union[str, Callable[[GraphQLResolveInfo], str]]] = None,
        cache_ttl: Optional[int] = None,
    ):
        parsed_template = parse(template)

        self._template = validate_template(parsed_template)
        self._operation_name = cast(NameNode, self._template.name).value
        self._path = find_path_in_template(self._template.selection_set)

        if variables is not None:
            self._variables = variables
        else:
            self._variables = get_variables_from_template(self._template)

        super().__init__(url, proxy_headers, cache, cache_key, cache_ttl)

    async def __call__(self, obj: Any, info: GraphQLResolveInfo, **arguments) -> Any:
        operation_node = make_final_operation(self._template, info)

        if isinstance(obj, dict):
            data = obj.get(info.field_name)
        else:
            data = getattr(obj, info.field_name)

        variables = {}
        if self._variables:
            for attr_name, var_name in self._variables.items():
                if isinstance(data, dict):
                    variables[var_name] = data.get(attr_name)
                else:
                    variables[var_name] = getattr(data, attr_name)

        payload = {
            "operationName": self._operation_name,
            "query": print_ast(operation_node),
            "variables": variables,
        }

        if self._cache:
            return await self.proxy_query_with_cache(
                data, info, payload, operation_node
            )

        return await self.proxy_query(data, info, payload)

    def get_field_data(self, info: GraphQLResolveInfo, data: dict) -> Optional[Any]:
        for field_name in self._path:
            if field_name in data:
                data = data[field_name]
            else:
                return None

        return data


def validate_template(template: DocumentNode) -> OperationDefinitionNode:
    if len(template.definitions) != 1:
        raise ValueError("Query template must define single operation.")

    if not isinstance(template.definitions[0], OperationDefinitionNode):
        raise ValueError("Query template must define single operation.")

    if not template.definitions[0].name:
        raise ValueError("Query template operation must be named.")

    placeholder_count = count_template_fields_placeholders(
        template.definitions[0].selection_set
    )

    if placeholder_count != 1:
        raise ValueError(
            "Query template operation should specify one "
            f"'{FIELDS_PLACEHOLDER}' "
            f"placeholder. It specifies {placeholder_count}."
        )

    return template.definitions[0]


def count_template_fields_placeholders(selection_set: SelectionSetNode) -> int:
    results = 0

    for node in selection_set.selections:
        if not isinstance(node, FieldNode):
            raise ValueError("Template can't use fragments")

        if node.name.value == FIELDS_PLACEHOLDER:
            if node.selection_set:
                raise ValueError("Query template '__FIELDS' can't have selection set")

            results += 1

        elif node.selection_set:
            results += count_template_fields_placeholders(node.selection_set)

    return results


def find_path_in_template(selection_set: SelectionSetNode) -> List[str]:
    for node in selection_set.selections:
        if not isinstance(node, FieldNode):
            raise ValueError("Template can't use fragments")

        if node.selection_set:
            path = find_path_in_template(node.selection_set)
            if path is not None:
                return [node.name.value] + path

        if node.name.value == "__FIELDS":
            return []

    return []


def make_final_operation(
    template: OperationDefinitionNode,
    info: GraphQLResolveInfo,
) -> OperationDefinitionNode:
    return OperationDefinitionNode(
        name=template.name,
        directives=template.directives,
        variable_definitions=template.variable_definitions,
        operation=template.operation,
        selection_set=copy_selection_set(template.selection_set, info),
    )


def copy_selection_set(
    selection_set: SelectionSetNode,
    info: GraphQLResolveInfo,
) -> SelectionSetNode:
    if len(selection_set.selections) == 1:
        node = selection_set.selections[0]
        if isinstance(node, FieldNode) and node.name.value == "__FIELDS":
            for field in info.field_nodes:
                if isinstance(field, FieldNode) and field.name.value == info.field_name:
                    return copy_selection_set(
                        cast(SelectionSetNode, field.selection_set),
                        info,
                    )

    selections: List[SelectionNode] = []
    for node in selection_set.selections:
        if isinstance(node, FieldNode):
            selections.append(copy_template_field(node, info))

        if isinstance(node, FragmentSpreadNode):
            fragment = info.fragments[node.name.value]
            selections.extend(
                copy_selection_set(fragment.selection_set, info).selections
            )

    return SelectionSetNode(selections=tuple(selections))


def copy_template_field(field: FieldNode, info: GraphQLResolveInfo) -> FieldNode:
    if field.selection_set:
        selection_set = copy_selection_set(field.selection_set, info)
    else:
        selection_set = None

    return FieldNode(
        alias=field.alias,
        name=field.name,
        arguments=field.arguments,
        selection_set=selection_set,
    )


def get_variables_from_template(template: OperationDefinitionNode) -> Dict[str, str]:
    variables = {}

    if template.variable_definitions:
        for variable_definition in template.variable_definitions:
            variable_name = variable_definition.variable.name.value
            variables[variable_name] = variable_name

    return variables
