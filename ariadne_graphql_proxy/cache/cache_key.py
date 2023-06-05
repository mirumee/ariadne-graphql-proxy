import hashlib
from typing import Any, Callable, Dict, Optional, Union

from graphql import (
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLResolveInfo,
    InlineFragmentNode,
    OperationDefinitionNode,
    SelectionNode,
    print_ast,
)


def get_info_cache_key(
    obj: Any,
    info: GraphQLResolveInfo,
    arguments: Optional[Dict[str, Any]],
    prefix: Optional[Union[str, Callable[[GraphQLResolveInfo], str]]] = None,
) -> str:
    """Builds cache key unique to this resolver call using its info.

    Used for resolvers that forward GraphQL calls to other GraphQL services.

    Cache key is seeded with:

    - `obj` representation
    - fields from GraphQL query
    - arguments values
    """
    cache_hash = hashlib.md5(
        ",".join(
            [
                get_obj_cache_seed(obj),
                get_info_cache_seed(info),
                get_arguments_cache_seed(arguments),
            ]
        ).encode("utf-8")
    ).hexdigest()

    cache_prefix = get_cache_prefix(info, prefix)
    if cache_prefix:
        return f"{cache_prefix}_{cache_hash}"

    return cache_hash


def get_operation_cache_key(
    obj: Any,
    info: GraphQLResolveInfo,
    operation: OperationDefinitionNode,
    arguments: Optional[Dict[str, Any]],
    prefix: Optional[Union[str, Callable[[GraphQLResolveInfo], str]]] = None,
) -> str:
    """Builds cache key unique to this resolver call using its operation definition.

    Used for resolvers that forward GraphQL calls to other GraphQL services.

    Cache key is seeded with:

    - `obj` representation
    - fields from GraphQL query
    - arguments values
    """
    cache_hash = hashlib.md5(
        ",".join(
            [
                get_obj_cache_seed(obj),
                get_operation_cache_seed(operation),
                get_arguments_cache_seed(arguments),
            ]
        ).encode("utf-8")
    ).hexdigest()

    cache_prefix = get_cache_prefix(info, prefix)
    if cache_prefix:
        return f"{cache_prefix}_{cache_hash}"

    return cache_hash


def get_simple_cache_key(
    obj: Any,
    info: GraphQLResolveInfo,
    arguments: Optional[Dict[str, Any]],
    prefix: Optional[Union[str, Callable[[GraphQLResolveInfo], str]]] = None,
) -> str:
    """Builds cache key unique for given `obj` and `arguments`.

    Used for resolvers that retrieve data from sources that

    Cache key is seeded with:

    - `obj` representation
    - arguments values
    """
    cache_hash = hashlib.md5(
        ",".join(
            [
                get_obj_cache_seed(obj),
                get_arguments_cache_seed(arguments),
            ]
        ).encode("utf-8")
    ).hexdigest()

    cache_prefix = get_cache_prefix(info, prefix)
    if cache_prefix:
        return f"{cache_prefix}_{cache_hash}"

    return cache_hash


def get_cache_prefix(
    info: GraphQLResolveInfo,
    prefix: Optional[Union[str, Callable[[GraphQLResolveInfo], str]]],
) -> Optional[str]:
    if callable(prefix):
        return prefix(info)
    return prefix or None


def get_obj_cache_seed(obj: Any) -> str:
    if obj is None:
        return ""

    return repr(obj)


def get_info_cache_seed(info: GraphQLResolveInfo) -> str:
    fields = sorted(
        [get_flattened_node(node, info.fragments) for node in info.field_nodes]
    )

    return ",".join(fields)


def get_operation_cache_seed(operation: OperationDefinitionNode) -> str:
    fields = sorted(
        [get_flattened_node(node, {}) for node in operation.selection_set.selections]
    )

    return ",".join(fields)


def get_flattened_node(
    node: SelectionNode,
    fragments: Dict[str, FragmentDefinitionNode],
) -> str:
    if isinstance(node, FieldNode):
        return get_flattened_field(node, fragments)
    if isinstance(node, InlineFragmentNode):
        return get_flattened_inline_fragment(node, fragments)
    if isinstance(node, FragmentSpreadNode):
        return get_flattened_fragment(node, fragments)

    raise ValueError(f"Invalid SelectionNode: {type(node).__name__}")


def get_flattened_field(
    field_node: FieldNode,
    fragments: Dict[str, FragmentDefinitionNode],
) -> str:
    flat_field = field_node.name.value

    if field_node.arguments:
        field_args = sorted(
            [
                f"{argument.name.value}: " + print_ast(argument.value)
                for argument in field_node.arguments
            ]
        )
        flat_field += f"({','.join(field_args)})"

    if field_node.selection_set:
        selections = []
        for sub_field_node in field_node.selection_set.selections:
            selections.append(get_flattened_node(sub_field_node, fragments))
        flat_field += "{" + ",".join(sorted(selections)) + "}"

    return flat_field


def get_flattened_inline_fragment(
    node: InlineFragmentNode,
    fragments: Dict[str, FragmentDefinitionNode],
) -> str:
    flat_fragment = f"... on {print_ast(node.type_condition)}"

    selections = []
    for child_node in node.selection_set.selections:
        selections.append(get_flattened_node(child_node, fragments))

    flat_fragment += "{" + ",".join(sorted(selections)) + "}"
    return flat_fragment


def get_flattened_fragment(
    node: FragmentSpreadNode,
    fragments: Dict[str, FragmentDefinitionNode],
) -> str:
    fragment = fragments[node.name.value]

    fields = sorted(
        [
            get_flattened_node(node, fragments)
            for node in fragment.selection_set.selections
        ]
    )

    return ",".join(fields)


def get_arguments_cache_seed(arguments: Optional[Dict[str, Any]]) -> str:
    if not arguments:
        return ""

    args = [f"{key}={repr(arguments[key])}" for key in sorted(arguments)]

    return repr(args)
