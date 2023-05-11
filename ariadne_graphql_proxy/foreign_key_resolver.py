from typing import Any, Callable, Dict, List, Optional, Union

from graphql import (
    FieldNode,
    FragmentSpreadNode,
    GraphQLResolveInfo,
    OperationDefinitionNode,
    SelectionSetNode,
    parse,
)

from .proxy_resolver import ProxyResolver
from .print import print_operation
from .cache import CacheBackend


class ForeignKeyResolver(ProxyResolver):
    _template: OperationDefinitionNode
    _operation_name: str
    _path: List[str]
    _variables: Optional[Dict[str, str]]

    def __init__(
        self,
        url: str,
        template: str,
        variables: Optional[Dict[str, str]],
        proxy_headers: Optional[Union[bool, List[str]]] = None,
        cache: Optional[CacheBackend] = None,
        cache_key: Optional[Union[str, Callable[[GraphQLResolveInfo], str]]] = None,
        cache_ttl: Optional[int] = None,
    ):
        parsed_template = parse(template)
        if len(parsed_template.definitions) != 1:
            raise ValueError("Query template must define a single operation.")
        if not isinstance(parsed_template.definitions[0], OperationDefinitionNode):
            raise ValueError("Query template must define a single operation.")
        if not parsed_template.definitions[0].name:
            raise ValueError("Query template operation must be named.")

        self._template = parsed_template.definitions[0]
        self._operation_name = self._template.name.value
        self._path = find_path_in_template(self._template.selection_set)
        self._variables = variables

        if not self._path:
            raise ValueError(
                "Query template operation must have single '__FIELDS' node."
            )

        super().__init__(url, proxy_headers, cache, cache_key, cache_ttl)

    async def __call__(self, data: Any, info: GraphQLResolveInfo) -> Any:
        operation_node = make_final_operation(self._template, info)

        if isinstance(data, dict):
            obj = data.get(info.field_name)
        else:
            obj = getattr(data, info.field_name)

        variables = {}
        if self._variables:
            for attr_name, var_name in self._variables.items():
                if isinstance(obj, dict):
                    variables[var_name] = obj.get(attr_name)
                else:
                    variables[var_name] = getattr(obj, attr_name)

        payload = {
            "operationName": self._operation_name,
            "query": print_operation(operation_node),
            "variables": variables,
        }

        if self._cache:
            return await self.proxy_query_with_cache(obj, info, payload, operation_node)

        return await self.proxy_query(obj, info, payload)

    def get_field_data(self, info: GraphQLResolveInfo, data: dict) -> Optional[Any]:
        for field_name in self._path:
            if field_name in data:
                data = data[field_name]
            else:
                return None

        return data


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
                    return copy_selection_set(field.selection_set, info)

    selections = []
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
