import hashlib
from typing import Any, Dict, Optional, Union

from graphql import (
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLResolveInfo,
)

from ..print import print_value


def get_cache_key(
    obj: Any, info: GraphQLResolveInfo, arguments: Any, prefix: Optional[str] = None
) -> str:
    """Builds cache key unique to this resolver call.

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
                get_fields_cache_seed(info),
                get_arguments_cache_seed(arguments),
            ]
        ).encode("utf-8")
    ).hexdigest()
    if prefix:
        return f"{prefix}_{cache_hash}"

    return cache_hash


def get_simple_cache_key(obj: Any, arguments: Any, prefix: Optional[str] = None) -> str:
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
    if prefix:
        return f"{prefix}_{cache_hash}"

    return cache_hash


def get_obj_cache_seed(obj: Any) -> str:
    if obj is None:
        return ""

    return repr(obj)


def get_fields_cache_seed(info: GraphQLResolveInfo) -> str:
    fields = sorted(
        [get_flattened_node(node, info.fragments) for node in info.field_nodes]
    )

    return ",".join(fields)


def get_flattened_node(
    node: Union[FieldNode, FragmentSpreadNode],
    fragments: Dict[str, FragmentDefinitionNode],
) -> str:
    if isinstance(node, FieldNode):
        return get_flattened_field(node, fragments)
    if isinstance(node, FragmentSpreadNode):
        return get_flattened_fragment(node, fragments)


def get_flattened_field(
    field_node: FieldNode,
    fragments: Dict[str, FragmentDefinitionNode],
) -> str:
    flat_field = field_node.name.value

    if field_node.arguments:
        field_args = sorted(
            [
                f"{argument.name.value}: " + print_value(argument.value)
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


def get_arguments_cache_seed(arguments: Optional[dict]) -> str:
    if not arguments:
        return ""

    args = [f"{key}={repr(arguments[key])}" for key in sorted(arguments)]

    return repr(args)
