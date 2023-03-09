from typing import Dict, List, Optional, Set, Tuple, cast

from graphql import (
    DocumentNode,
    FieldNode,
    FragmentSpreadNode,
    FragmentDefinitionNode,
    GraphQLSchema,
    NameNode,
    OperationDefinitionNode,
    SelectionSetNode,
)


class QueryFilterContext:
    schema_id: int
    fragments: Dict[str, FragmentDefinitionNode]

    def __init__(self, schema_id: int):
        self.schema_id = schema_id
        self.fragments = {}


class QueryFilter:
    def __init__(
        self,
        schema: GraphQLSchema,
        schemas: List[GraphQLSchema],
        fields_map: Dict[str, Dict[str, Set[int]]],
        fields_types: Dict[str, Dict[str, str]],
        foreign_keys: Dict[str, Dict[str, List[List[str]]]],
    ):
        self.schema = schema
        self.schemas = schemas
        self.fields_map = fields_map
        self.fields_types = fields_types
        self.foreign_keys = foreign_keys

    def split_query(self, document: DocumentNode) -> List[Tuple[int, DocumentNode]]:
        queries: List[Tuple[int, DocumentNode]] = []

        for schema_id in range(len(self.schemas)):
            schema_query = self.get_schema_query(schema_id, document)
            if schema_query:
                queries.append((schema_id, schema_query))

        return queries

    def get_schema_query(
        self,
        schema_id: int,
        document: DocumentNode,
    ) -> Optional[DocumentNode]:
        context = QueryFilterContext(schema_id)
        definitions = []

        for definition_node in document.definitions:
            if isinstance(definition_node, FragmentDefinitionNode):
                fragment_node = cast(FragmentDefinitionNode, definition_node)
                new_fragment = self.filter_fragment_node(fragment_node, context)
                if new_fragment:
                    context.fragments[new_fragment.name.value] = new_fragment

        for definition_node in document.definitions:
            if isinstance(definition_node, OperationDefinitionNode):
                operation_node = cast(OperationDefinitionNode, definition_node)
                new_operation = self.filter_operation_node(
                    operation_node,
                    context,
                )
                if new_operation:
                    definitions.append(new_operation)

        if not definitions:
            return None

        for fragment in context.fragments.values():
            final_fragment = self.filter_fragment_node_fields(fragment, context)
            if final_fragment:
                definitions.append(final_fragment)

        return DocumentNode(definitions=tuple(definitions))

    def filter_fragment_node(
        self,
        fragment_node: FragmentDefinitionNode,
        context: QueryFilterContext,
    ) -> Optional[FragmentDefinitionNode]:
        type_name = fragment_node.type_condition.name.value.title()
        if type_name not in self.fields_map:
            return None

        type_fields = self.fields_map[type_name]

        new_selections = []
        for selection in fragment_node.selection_set.selections:
            if isinstance(selection, FragmentSpreadNode):
                new_selections.append(selection)
                continue

            if (
                selection.name.value not in type_fields
                or context.schema_id not in type_fields[selection.name.value]
            ):
                continue

            filtered_selection = self.filter_field_node(
                selection,
                type_name,
                context,
                filter_fragments=False,
            )

            if filtered_selection:
                new_selections.append(filtered_selection)

        if not new_selections:
            return None

        return FragmentDefinitionNode(
            name=fragment_node.name,
            type_condition=fragment_node.type_condition,
            directives=fragment_node.directives,
            selection_set=SelectionSetNode(
                selections=tuple(new_selections),
            ),
        )

    def filter_operation_node(
        self,
        operation_node: OperationDefinitionNode,
        context: QueryFilterContext,
    ) -> Optional[OperationDefinitionNode]:
        type_name = operation_node.operation.value.title()
        if type_name not in self.fields_map:
            return None

        type_fields = self.fields_map[type_name]
        new_selections = []

        for selection in operation_node.selection_set.selections:
            if isinstance(selection, FieldNode):
                if (
                    selection.name.value not in type_fields
                    or context.schema_id not in type_fields[selection.name.value]
                ):
                    continue

                filtered_selection = self.filter_field_node(
                    selection,
                    type_name,
                    context,
                    filter_fragments=True,
                )

                if filtered_selection:
                    new_selections.append(filtered_selection)

            if isinstance(selection, FragmentSpreadNode):
                new_selections.append(selection)

        if not new_selections:
            return None

        return OperationDefinitionNode(
            loc=operation_node.loc,
            operation=operation_node.operation,
            name=operation_node.name,
            directives=operation_node.directives,
            variable_definitions=operation_node.variable_definitions,
            selection_set=SelectionSetNode(
                selections=tuple(new_selections),
            ),
        )

    def filter_field_node(
        self,
        field_node: FieldNode,
        schema_obj: str,
        context: QueryFilterContext,
        filter_fragments: bool,
    ) -> Optional[FieldNode]:
        if not field_node.selection_set:
            return field_node

        field_name = field_node.name.value

        if (
            schema_obj in self.foreign_keys
            and field_name in self.foreign_keys[schema_obj]
        ):
            foreign_key = tuple(
                FieldNode(
                    loc=field_node.loc,
                    name=NameNode(value=on_name),
                )
                for on_name in self.foreign_keys[schema_obj][field_name]
            )

            return FieldNode(
                loc=field_node.loc,
                directives=field_node.directives,
                alias=field_node.alias,
                name=field_node.name,
                arguments=field_node.arguments,
                selection_set=SelectionSetNode(selections=foreign_key),
            )

        type_name = self.fields_types[schema_obj][field_name]
        type_fields = self.fields_map[type_name]

        new_selections = []
        for selection in field_node.selection_set.selections:
            if isinstance(selection, FieldNode):
                if (
                    selection.name.value not in type_fields
                    or context.schema_id not in type_fields[selection.name.value]
                ):
                    continue

                filtered_selection = self.filter_field_node(
                    selection,
                    type_name,
                    context,
                    filter_fragments=filter_fragments,
                )

                if filtered_selection:
                    new_selections.append(filtered_selection)

            if isinstance(selection, FragmentSpreadNode):
                if not filter_fragments or selection.name.value in context.fragments:
                    new_selections.append(selection)

        if not new_selections:
            return None

        return FieldNode(
            loc=field_node.loc,
            directives=field_node.directives,
            alias=field_node.alias,
            name=field_node.name,
            arguments=field_node.arguments,
            selection_set=SelectionSetNode(selections=tuple(new_selections)),
        )

    def filter_fragment_node_fields(
        self,
        fragment_node: FragmentDefinitionNode,
        context: QueryFilterContext,
    ) -> Optional[FragmentDefinitionNode]:
        new_selections = []
        for selection in fragment_node.selection_set.selections:
            if isinstance(selection, FieldNode):
                new_field_node = self.filter_fragment_field_fragments(
                    selection, context
                )
                if new_field_node:
                    new_selections.append(selection)

            if isinstance(selection, FragmentSpreadNode):
                if selection.name.value in context.fragments:
                    new_selections.append(selection)

        if not new_selections:
            return None

        fragment_node.selection_set.selections = tuple(new_selections)
        return fragment_node

    def filter_fragment_field_fragments(
        self,
        field_node: FieldNode,
        context: QueryFilterContext,
    ) -> Optional[FieldNode]:
        if not field_node.selection_set:
            return field_node

        new_selections = []
        for selection in field_node.selection_set.selections:
            if isinstance(selection, FieldNode):
                new_field_node = self.filter_fragment_field_fragments(
                    selection, context
                )
                if new_field_node:
                    new_selections.append(selection)

            if isinstance(selection, FragmentSpreadNode):
                if selection.name.value in context.fragments:
                    new_selections.append(selection)

        if not new_selections:
            return None

        field_node.selection_set.selections = tuple(new_selections)
        return field_node
