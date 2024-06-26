from typing import Dict, List, Optional, Set, Tuple, cast

from graphql import (
    DocumentNode,
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLSchema,
    InlineFragmentNode,
    ListValueNode,
    NameNode,
    ObjectValueNode,
    OperationDefinitionNode,
    SelectionNode,
    SelectionSetNode,
    VariableNode,
)

from .selections import merge_selections


class QueryFilterContext:
    schema_id: int
    fragments: Dict[str, FragmentDefinitionNode]
    variables: Set[str]

    def __init__(self, schema_id: int):
        self.schema_id = schema_id
        self.fragments = {}
        self.variables = set()


class QueryFilter:
    def __init__(
        self,
        schema: GraphQLSchema,
        schemas: List[GraphQLSchema],
        fields_map: Dict[str, Dict[str, Set[int]]],
        fields_types: Dict[str, Dict[str, str]],
        unions: Dict[str, List[str]],
        foreign_keys: Dict[str, Dict[str, List[str]]],
        dependencies: Dict[int, Dict[str, Dict[str, SelectionSetNode]]],
    ):
        self.schema = schema
        self.schemas = schemas
        self.fields_map = fields_map
        self.fields_types = fields_types
        self.unions = unions
        self.foreign_keys = foreign_keys
        self.dependencies = dependencies

    def split_query(
        self, document: DocumentNode
    ) -> List[Tuple[int, DocumentNode, Set[str]]]:
        queries: List[Tuple[int, DocumentNode, Set[str]]] = []

        for schema_id in range(len(self.schemas)):
            schema_query, used_variables = self.get_schema_query_with_used_variables(
                schema_id, document
            )
            if schema_query:
                queries.append((schema_id, schema_query, used_variables))

        return queries

    def get_schema_query_with_used_variables(
        self,
        schema_id: int,
        document: DocumentNode,
    ) -> Tuple[Optional[DocumentNode], Set[str]]:
        context = QueryFilterContext(schema_id)
        definitions = []

        for definition_node in document.definitions:
            if isinstance(definition_node, FragmentDefinitionNode):
                fragment_node = cast(FragmentDefinitionNode, definition_node)
                context.fragments[fragment_node.name.value] = fragment_node

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
            return None, context.variables

        return DocumentNode(definitions=tuple(definitions)), context.variables

    def filter_operation_node(
        self,
        operation_node: OperationDefinitionNode,
        context: QueryFilterContext,
    ) -> Optional[OperationDefinitionNode]:
        type_name = operation_node.operation.value.title()
        if type_name not in self.fields_map:
            return None

        type_fields = self.fields_map[type_name]
        new_selections: List[SelectionNode] = []

        for selection in operation_node.selection_set.selections:
            if isinstance(selection, FieldNode):
                if (
                    selection.name.value not in type_fields
                    or context.schema_id not in type_fields[selection.name.value]
                ):
                    continue

                field_selection = self.filter_field_node(selection, type_name, context)

                if field_selection:
                    new_selections.append(field_selection)

            if isinstance(selection, InlineFragmentNode):
                inline_fragment_selection = self.filter_inline_fragment_node(
                    selection, type_name, context
                )

                if inline_fragment_selection:
                    new_selections.append(inline_fragment_selection)

            if isinstance(selection, FragmentSpreadNode):
                new_selections += self.filter_fragment_spread_node(
                    selection, type_name, context
                )

        if not new_selections:
            return None

        used_variable_definitions = [
            variable_definition
            for variable_definition in operation_node.variable_definitions
            if variable_definition.variable.name.value in context.variables
        ]

        return OperationDefinitionNode(
            loc=operation_node.loc,
            operation=operation_node.operation,
            name=operation_node.name,
            directives=operation_node.directives,
            variable_definitions=tuple(used_variable_definitions),
            selection_set=SelectionSetNode(
                selections=tuple(new_selections),
            ),
        )

    def filter_field_node(
        self,
        field_node: FieldNode,
        schema_obj: str,
        context: QueryFilterContext,
    ) -> Optional[FieldNode]:
        self.update_context_variables(field_node, context)
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
        type_is_union = type_name in self.unions

        if type_is_union:
            type_fields = {}
        else:
            type_fields = self.fields_map[type_name]

        fields_dependencies = self.get_type_fields_dependencies(
            context.schema_id, type_name
        )

        new_selections: List[SelectionNode] = []
        for selection in field_node.selection_set.selections:
            if isinstance(selection, FieldNode):
                field_name = selection.name.value
                if fields_dependencies and field_name in fields_dependencies:
                    new_selections = merge_selections(
                        new_selections, fields_dependencies[field_name].selections
                    )

                if (
                    field_name not in type_fields
                    or context.schema_id not in type_fields[field_name]
                ):
                    continue

                field_selection = self.filter_field_node(selection, type_name, context)

                if field_selection:
                    new_selections.append(field_selection)

            if isinstance(selection, InlineFragmentNode):
                inline_fragment_selection = self.filter_inline_fragment_node(
                    selection, type_name, context
                )

                if inline_fragment_selection:
                    new_selections.append(inline_fragment_selection)

            if isinstance(selection, FragmentSpreadNode):
                if type_is_union:
                    inline_fragment = self.inline_fragment_spread_node(
                        selection, schema_obj, context
                    )
                    if inline_fragment:
                        new_selections.append(inline_fragment)
                else:
                    new_selections += self.filter_fragment_spread_node(
                        selection, schema_obj, context
                    )

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

    def filter_inline_fragment_node(
        self,
        fragment_node: InlineFragmentNode,
        schema_obj: str,
        context: QueryFilterContext,
    ) -> Optional[InlineFragmentNode]:
        type_name = fragment_node.type_condition.name.value
        type_fields = self.fields_map[type_name]

        fields_dependencies = self.get_type_fields_dependencies(
            context.schema_id, type_name
        )

        new_selections: List[SelectionNode] = []
        for selection in fragment_node.selection_set.selections:
            if isinstance(selection, FieldNode):
                field_name = selection.name.value
                if fields_dependencies and field_name in fields_dependencies:
                    new_selections = merge_selections(
                        new_selections, fields_dependencies[field_name].selections
                    )

                if (
                    field_name not in type_fields
                    or context.schema_id not in type_fields[field_name]
                ):
                    continue

                field_selection = self.filter_field_node(selection, type_name, context)

                if field_selection:
                    new_selections.append(field_selection)

            if isinstance(selection, InlineFragmentNode):
                inline_fragment_selection = self.filter_inline_fragment_node(
                    selection, type_name, context
                )

                if inline_fragment_selection:
                    new_selections.append(inline_fragment_selection)

            if isinstance(selection, FragmentSpreadNode):
                new_selections += self.filter_fragment_spread_node(
                    selection, schema_obj, context
                )

        if not new_selections:
            return None

        return InlineFragmentNode(
            type_condition=fragment_node.type_condition,
            selection_set=SelectionSetNode(selections=tuple(new_selections)),
        )

    def filter_fragment_spread_node(
        self,
        fragment_node: FragmentSpreadNode,
        schema_obj: str,
        context: QueryFilterContext,
    ) -> List[SelectionNode]:
        fragment_name = fragment_node.name.value
        fragment = context.fragments.get(fragment_name)

        if not fragment:
            return []

        type_name = fragment.type_condition.name.value
        type_fields = self.fields_map[type_name]

        fields_dependencies = self.get_type_fields_dependencies(
            context.schema_id, type_name
        )

        new_selections: List[SelectionNode] = []
        for selection in fragment.selection_set.selections:
            if isinstance(selection, FieldNode):
                field_name = selection.name.value
                if fields_dependencies and field_name in fields_dependencies:
                    new_selections = merge_selections(
                        new_selections, fields_dependencies[field_name].selections
                    )

                if (
                    field_name not in type_fields
                    or context.schema_id not in type_fields[field_name]
                ):
                    continue

                field_selection = self.filter_field_node(selection, type_name, context)

                if field_selection:
                    new_selections.append(field_selection)

            if isinstance(selection, InlineFragmentNode):
                inline_fragment_selection = self.filter_inline_fragment_node(
                    selection, type_name, context
                )

                if inline_fragment_selection:
                    new_selections.append(inline_fragment_selection)

            if isinstance(selection, FragmentSpreadNode):
                new_selections += self.filter_fragment_spread_node(
                    selection, schema_obj, context
                )

        return new_selections

    def inline_fragment_spread_node(
        self,
        fragment_node: FragmentSpreadNode,
        schema_obj: str,
        context: QueryFilterContext,
    ) -> Optional[InlineFragmentNode]:
        fragment_name = fragment_node.name.value
        fragment = context.fragments.get(fragment_name)
        if not fragment:
            return None

        selections = self.filter_fragment_spread_node(
            fragment_node, schema_obj, context
        )

        if not selections:
            return None

        return InlineFragmentNode(
            type_condition=fragment.type_condition,
            selection_set=SelectionSetNode(
                selections=tuple(selections),
            ),
        )

    def get_type_fields_dependencies(
        self,
        schema_id: int,
        type_name: str,
    ) -> Optional[Dict[str, SelectionSetNode]]:
        if schema_id in self.dependencies and type_name in self.dependencies[schema_id]:
            return self.dependencies[schema_id][type_name]

        return None

    def update_context_variables(
        self, field_node: FieldNode, context: QueryFilterContext
    ):
        for argument in field_node.arguments:
            self.extract_variables(argument.value, context)  # type: ignore

    def extract_variables(
        self,
        value: VariableNode | ListValueNode | ObjectValueNode,
        context: QueryFilterContext,
    ):
        if isinstance(value, VariableNode):
            context.variables.add(value.name.value)
        elif isinstance(value, ObjectValueNode):
            for field in value.fields:
                self.extract_variables(field.value, context)  # type: ignore
        elif isinstance(value, ListValueNode):
            for item in value.values:
                self.extract_variables(item, context)  # type: ignore
