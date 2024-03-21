from typing import Dict, Sequence, List, cast

from graphql import FieldNode, SelectionNode, SelectionSetNode


def merge_selection_sets(
    set_a: SelectionSetNode, set_b: SelectionSetNode
) -> SelectionSetNode:
    return SelectionSetNode(
        selections=tuple(merge_selections(set_a.selections, set_b.selections)),
    )


def merge_selections(
    set_a: Sequence[SelectionNode], set_b: Sequence[SelectionNode]
) -> List[SelectionNode]:
    final_set: List[SelectionNode] = list(set_a)

    index: Dict[str, int] = {}
    for i, field in enumerate(final_set):
        if isinstance(field, FieldNode):
            index[(field.alias or field.name).value] = i

    for field in set_b:
        if isinstance(field, FieldNode):
            field_name = (field.alias or field.name).value
            if field_name in index:
                field_index = index[field_name]
                other_field = cast(FieldNode, final_set[field_index])
                if other_field.selection_set and field.selection_set:
                    final_set[field_index] = FieldNode(
                        directives=other_field.directives,
                        alias=other_field.alias,
                        name=field.name,
                        arguments=other_field.arguments,
                        selection_set=merge_selection_sets(
                            other_field.selection_set, field.selection_set
                        ),
                    )
                elif other_field.selection_set or field.selection_set:
                    final_set[field_index] = FieldNode(
                        directives=other_field.directives,
                        alias=other_field.alias,
                        name=field.name,
                        arguments=other_field.arguments,
                        selection_set=(
                            other_field.selection_set or field.selection_set
                        ),
                    )
            else:
                final_set.append(field)

    return final_set
