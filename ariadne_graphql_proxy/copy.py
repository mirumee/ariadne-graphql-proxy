from copy import deepcopy
from typing import Dict, List, Optional, Set, Tuple, Union, cast

from graphql import (
    DirectiveNode,
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLDirective,
    GraphQLEnumType,
    GraphQLField,
    GraphQLFloat,
    GraphQLID,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInt,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNamedType,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLString,
    GraphQLUnionType,
    assert_valid_schema,
)

from .standard_types import STANDARD_DIRECTIVES, STANDARD_TYPES
from .output_types import unwrap_output_type


ROOTS_ARGS_NAMES = {
    "Query": "queries",
    "Mutation": "mutations",
    "Subscription": "subscriptions",
}


def copy_schema(
    schema: GraphQLSchema,
    *,
    queries: Optional[List[str]] = None,
    mutations: Optional[List[str]] = None,
    subscriptions: Optional[List[str]] = None,
    exclude_types: Optional[List[str]] = None,
    exclude_args: Optional[Dict[str, Dict[str, List[str]]]] = None,
    exclude_fields: Optional[Dict[str, List[str]]] = None,
    exclude_directives: Optional[List[str]] = None,
    exclude_directives_args: Optional[Dict[str, List[str]]] = None,
) -> GraphQLSchema:
    if queries or mutations or subscriptions:
        return copy_schema_with_subset(
            schema,
            queries=queries or {},
            mutations=mutations or {},
            subscriptions=subscriptions or {},
            exclude_types=_copy_arg(exclude_types, []),
            exclude_args=_copy_arg(exclude_args, {}),
            exclude_fields=_copy_arg(exclude_fields, {}),
            exclude_directives=_copy_arg(exclude_directives, []),
            exclude_directives_args=_copy_arg(exclude_directives_args, {}),
        )

    new_types = copy_schema_types(
        schema,
        exclude_types=exclude_types,
        exclude_args=exclude_args,
        exclude_fields=exclude_fields,
    )

    query_type = None
    if schema.query_type:
        query_type = new_types[schema.query_type.name]

    mutation_type = None
    if schema.mutation_type and schema.mutation_type.name in new_types:
        mutation_type = new_types[schema.mutation_type.name]

    new_directives = copy_directives(
        new_types,
        schema.directives,
        exclude_directives=exclude_directives,
        exclude_directives_args=exclude_directives_args,
    )

    new_schema = GraphQLSchema(
        query=query_type,
        mutation=mutation_type,
        types=new_types.values(),
        directives=new_directives,
    )
    assert_valid_schema(new_schema)
    return new_schema


def _copy_arg(arg, default):
    return deepcopy(arg) if arg else default


def copy_schema_with_subset(
    schema: GraphQLSchema,
    *,
    queries: List[str],
    mutations: List[str],
    subscriptions: List[str],
    exclude_types: List[str],
    exclude_args: Dict[str, Dict[str, List[str]]],
    exclude_fields: Dict[str, List[str]],
    exclude_directives: List[str],
    exclude_directives_args: Dict[str, List[str]],
) -> GraphQLSchema:
    roots_dependencies = find_roots_dependencies(
        schema,
        {
            "Query": queries or [],
            "Mutation": mutations or [],
            "Subscription": subscriptions or [],
        },
        exclude_types,
        exclude_args,
        exclude_fields,
        exclude_directives,
        exclude_directives_args,
    )

    for schema_type in schema.type_map:
        if schema_type not in STANDARD_TYPES and schema_type not in roots_dependencies:
            exclude_types.append(schema_type)

    for schema_directive in schema.directives:
        directive_name = schema_directive.name
        if (
            directive_name not in STANDARD_DIRECTIVES
            and directive_name not in roots_dependencies
        ):
            exclude_directives.append(directive_name)

    if queries:
        exclude_fields.setdefault("Query", [])
        if schema.query_type:
            for field_name in schema.query_type.fields:
                if field_name not in queries:
                    exclude_fields["Query"].append(field_name)

    if mutations:
        exclude_fields.setdefault("Mutation", [])
        if schema.mutation_type:
            for field_name in schema.mutation_type.fields:
                if field_name not in mutations:
                    exclude_fields["Mutation"].append(field_name)

    new_types = copy_schema_types(
        schema,
        exclude_types=exclude_types,
        exclude_args=exclude_args,
        exclude_fields=exclude_fields,
    )

    query_type = None
    if schema.query_type:
        query_type = new_types[schema.query_type.name]

    mutation_type = None
    if schema.mutation_type and schema.mutation_type.name in new_types:
        mutation_type = new_types[schema.mutation_type.name]

    new_directives = copy_directives(
        new_types,
        schema.directives,
        exclude_directives=exclude_directives,
        exclude_directives_args=exclude_directives_args,
    )

    new_schema = GraphQLSchema(
        query=query_type,
        mutation=mutation_type,
        types=new_types.values(),
        directives=new_directives,
    )
    assert_valid_schema(new_schema)
    return new_schema


def find_roots_dependencies(
    schema: GraphQLSchema,
    roots: Dict[str, List[str]],
    exclude_types: Optional[List[str]] = None,
    exclude_args: Optional[Dict[str, Dict[str, List[str]]]] = None,
    exclude_fields: Optional[Dict[str, List[str]]] = None,
    exclude_directives: Optional[List[str]] = None,
    exclude_directives_args: Optional[Dict[str, List[str]]] = None,
) -> List[str]:
    visitor = TypesDependenciesVisitor(
        schema,
        exclude_types,
        exclude_args,
        exclude_fields,
        exclude_directives,
        exclude_directives_args,
    )

    return visitor.get_dependencies(roots)


class TypesDependenciesVisitor:
    def __init__(
        self,
        schema: GraphQLSchema,
        exclude_types: Optional[List[str]] = None,
        exclude_args: Optional[Dict[str, Dict[str, List[str]]]] = None,
        exclude_fields: Optional[Dict[str, List[str]]] = None,
        exclude_directives: Optional[List[str]] = None,
        exclude_directives_args: Optional[Dict[str, List[str]]] = None,
    ):
        self.schema = schema
        self.directives = {d.name: d for d in schema.directives}
        self.exclude_types = exclude_types
        self.exclude_args = exclude_args
        self.exclude_fields = exclude_fields
        self.exclude_directives = exclude_directives
        self.exclude_directives_args = exclude_directives_args

    def exclude_type(self, type_name: str) -> bool:
        return self.exclude_types and type_name in self.exclude_types

    def exclude_type_field(self, type_name: str, field_name: str) -> bool:
        return (
            self.exclude_fields
            and type_name in self.exclude_fields
            and field_name in self.exclude_fields[type_name]
        )

    def exclude_type_field_arg(
        self, type_name: str, field_name: str, arg_name: str
    ) -> bool:
        return (
            self.exclude_args
            and type_name in self.exclude_args
            and field_name in self.exclude_args[type_name]
            and arg_name in self.exclude_args[type_name][field_name]
        )

    def exclude_directive(self, type_name: str) -> bool:
        return self.exclude_directives and type_name in self.exclude_directives

    def exclude_directive_arg(self, type_name: str, arg_name: str) -> bool:
        return (
            self.exclude_directives_args
            and type_name in self.exclude_directives_args
            and arg_name in self.exclude_directives_args[type_name]
        )

    def get_dependencies(self, roots: Dict[str, List[str]]) -> List[str]:
        dependencies: Set[str] = set("Query")

        for root, fields in roots.items():
            if not fields:
                continue

            arg_name = ROOTS_ARGS_NAMES[root]
            dependencies.add(root)

            if root not in self.schema.type_map:
                raise ValueError(f"Root type '{root}' is not defined by the schema.")

            root_type = cast(GraphQLObjectType, self.schema.type_map[root])

            if root_type.ast_node:
                self.find_ast_directives_dependencies(
                    dependencies, root_type.ast_node.directives
                )

            for field_name in fields:
                if field_name not in root_type.fields:
                    raise ValueError(
                        f"Root type '{root}' is not defining the '{field_name}' field."
                    )

                if self.exclude_type_field(root, field_name):
                    raise ValueError(
                        f"Field '{field_name}' of type '{root}' is specified in both "
                        f"'exclude_fields' and '{arg_name}'."
                    )

                field = root_type.fields[field_name]
                field_type = unwrap_output_type(field.type)
                if self.exclude_type(field_type.name):
                    raise ValueError(
                        f"Field '{field_name}' of type '{root}' that is specified in "
                        f"'{arg_name}' has a return type '{field_type.name}' that is "
                        "also specified in 'exclude_types'."
                    )

                if field.ast_node:
                    self.find_ast_directives_dependencies(
                        dependencies, field.ast_node.directives
                    )

                self.find_type_dependencies(dependencies, field_type)

                for arg_name, arg in field.args.items():
                    if self.exclude_type_field_arg(root, field_name, arg_name):
                        continue

                    if arg.ast_node:
                        self.find_ast_directives_dependencies(
                            dependencies, arg.ast_node.directives
                        )

                    arg_type = unwrap_output_type(arg.type)
                    self.find_type_dependencies(dependencies, arg_type)

        return [dep for dep in dependencies if dep not in STANDARD_TYPES]

    def find_ast_directives_dependencies(
        self, dependencies: Set[str], directives_ast: Tuple[DirectiveNode]
    ):
        for directive in directives_ast:
            directive_name = directive.name.value
            directive_type = self.directives[directive_name]
            self.find_type_dependencies(dependencies, directive_type)

    def find_type_dependencies(
        self,
        dependencies: Set[str],
        type_def: GraphQLNamedType,
    ):
        if type_def.name in dependencies:
            return

        if isinstance(type_def, GraphQLDirective):
            self.find_directive_dependencies(dependencies, type_def)
            return

        if self.exclude_types and type_def.name in self.exclude_types:
            return

        dependencies.add(type_def.name)

        if isinstance(type_def, GraphQLEnumType):
            self.find_enum_type_dependencies(dependencies, type_def)

        if isinstance(type_def, GraphQLInputObjectType):
            self.find_input_type_dependencies(dependencies, type_def)

        if isinstance(type_def, (GraphQLObjectType, GraphQLInterfaceType)):
            self.find_object_type_dependencies(dependencies, type_def)

        if isinstance(type_def, GraphQLScalarType):
            self.find_scalar_type_dependencies(dependencies, type_def)

        if isinstance(type_def, GraphQLUnionType):
            self.find_union_type_dependencies(dependencies, type_def)

    def find_directive_dependencies(
        self,
        dependencies: Set[str],
        type_def: GraphQLDirective,
    ):
        if self.exclude_directive(type_def.name):
            return

        dependencies.add(type_def.name)

        for arg_name, arg in type_def.args.items():
            if self.exclude_directive_arg(type_def.name, arg_name):
                continue

            arg_type = unwrap_output_type(arg.type)
            self.find_type_dependencies(dependencies, arg_type)

    def find_enum_type_dependencies(
        self, dependencies: Set[str], type_def: GraphQLEnumType
    ):
        if type_def.ast_node:
            self.find_ast_directives_dependencies(
                dependencies, type_def.ast_node.directives
            )

        for value in type_def.values.values():
            if value.ast_node:
                self.find_ast_directives_dependencies(
                    dependencies, value.ast_node.directives
                )

    def find_input_type_dependencies(
        self, dependencies: Set[str], type_def: GraphQLInputObjectType
    ):
        if type_def.ast_node:
            self.find_ast_directives_dependencies(
                dependencies, type_def.ast_node.directives
            )

        for field_name, field in type_def.fields.items():
            if self.exclude_type_field(type_def.name, field_name):
                return

            if field.ast_node:
                self.find_ast_directives_dependencies(
                    dependencies, field.ast_node.directives
                )

            field_type = unwrap_output_type(field.type)
            self.find_type_dependencies(dependencies, field_type)

    def find_object_type_dependencies(
        self,
        dependencies: Set[str],
        type_def: Union[GraphQLObjectType, GraphQLInterfaceType],
    ):
        if type_def.ast_node:
            self.find_ast_directives_dependencies(
                dependencies, type_def.ast_node.directives
            )

        for interface in type_def.interfaces:
            self.find_type_dependencies(dependencies, interface)

        for field_name, field in type_def.fields.items():
            self.find_object_type_field_dependencies(
                dependencies, type_def, field_name, field
            )

    def find_object_type_field_dependencies(
        self,
        dependencies: Set[str],
        type_def: Union[GraphQLObjectType, GraphQLInterfaceType],
        field_name: str,
        field_def: GraphQLField,
    ):
        if self.exclude_type_field(type_def.name, field_name):
            return

        if field_def.ast_node:
            self.find_ast_directives_dependencies(
                dependencies, field_def.ast_node.directives
            )

        field_type = unwrap_output_type(field_def.type)
        self.find_type_dependencies(dependencies, field_type)

        for arg_name, arg in field_def.args.items():
            if self.exclude_type_field_arg(type_def.name, field_name, arg_name):
                continue

            if arg.ast_node:
                self.find_ast_directives_dependencies(
                    dependencies, arg.ast_node.directives
                )

            arg_type = unwrap_output_type(arg.type)
            self.find_type_dependencies(dependencies, arg_type)

    def find_scalar_type_dependencies(
        self, dependencies: Set[str], type_def: GraphQLScalarType
    ):
        if type_def.ast_node:
            self.find_ast_directives_dependencies(
                dependencies, type_def.ast_node.directives
            )

    def find_union_type_dependencies(
        self, dependencies: Set[str], type_def: GraphQLUnionType
    ):
        if type_def.ast_node:
            self.find_ast_directives_dependencies(
                dependencies, type_def.ast_node.directives
            )

        for union_type in type_def.types:
            self.find_type_dependencies(dependencies, union_type)


def copy_schema_types(
    schema: GraphQLSchema,
    exclude_types: Optional[List[str]] = None,
    exclude_args: Optional[Dict[str, Dict[str, List[str]]]] = None,
    exclude_fields: Optional[Dict[str, List[str]]] = None,
):
    exclude_types = exclude_types if exclude_types else []
    exclude_args = exclude_args if exclude_args else {}
    exclude_fields = exclude_fields if exclude_fields else {}
    new_types: dict = {}

    for graphql_type in schema.type_map.values():
        if graphql_type.name in STANDARD_TYPES or graphql_type.name in exclude_types:
            continue

        copied_type = copy_schema_type(
            new_types,
            graphql_type,
            exclude_types=exclude_types,
            object_exclude_fields=exclude_fields.get(graphql_type.name),
            object_exclude_args=exclude_args.get(graphql_type.name),
        )
        if copied_type:
            new_types[graphql_type.name] = copied_type

    return new_types


def copy_schema_type(
    new_types,
    graphql_type,
    exclude_types: Optional[List[str]] = None,
    object_exclude_fields: Optional[List[str]] = None,
    object_exclude_args: Optional[Dict[str, List[str]]] = None,
):
    if isinstance(graphql_type, GraphQLEnumType):
        return copy_enum(
            graphql_type,
            object_exclude_fields=object_exclude_fields,
        )

    if isinstance(graphql_type, GraphQLObjectType):
        return copy_object(
            new_types,
            graphql_type,
            object_exclude_fields=object_exclude_fields,
            object_exclude_args=object_exclude_args,
        )

    if isinstance(graphql_type, GraphQLInputObjectType):
        return copy_input(
            new_types,
            graphql_type,
            object_exclude_fields=object_exclude_fields,
        )

    if isinstance(graphql_type, GraphQLScalarType):
        return copy_scalar(graphql_type)

    if isinstance(graphql_type, GraphQLInterfaceType):
        return copy_interface(
            new_types,
            graphql_type,
            object_exclude_fields=object_exclude_fields,
            object_exclude_args=object_exclude_args,
        )

    if isinstance(graphql_type, GraphQLUnionType):
        return copy_union(new_types, graphql_type, exclude_types)

    raise TypeError(f"Can't copy unknown type '{repr(graphql_type)}'.")


def copy_enum(graphql_type, object_exclude_fields: Optional[List[str]] = None):
    object_exclude_fields = object_exclude_fields if object_exclude_fields else []
    values = {
        name: val
        for name, val in graphql_type.values.items()
        if name not in object_exclude_fields
    }
    return GraphQLEnumType(
        graphql_type.name,
        values,
        description=graphql_type.description,
        extensions=graphql_type.extensions,
    )


def copy_object(
    new_types,
    graphql_type,
    object_exclude_fields: Optional[List[str]] = None,
    object_exclude_args: Optional[Dict[str, List[str]]] = None,
):
    def fields_thunk():
        fields_to_exclude = object_exclude_fields if object_exclude_fields else []
        args_to_exclude = object_exclude_args if object_exclude_args else {}
        return {
            field_name: copy_field(new_types, field, args_to_exclude.get(field_name))
            for field_name, field in graphql_type.fields.items()
            if field_name not in fields_to_exclude
        }

    def interfaces_thunk():
        return [new_types[i.name] for i in graphql_type.interfaces]

    return GraphQLObjectType(
        name=graphql_type.name,
        fields=fields_thunk,
        interfaces=interfaces_thunk,
    )


def copy_field(
    new_types, graphql_field, field_exclude_args: Optional[List[str]] = None
):
    return GraphQLField(
        copy_field_type(new_types, graphql_field.type),
        copy_arguments(new_types, graphql_field.args, field_exclude_args),
        graphql_field.resolve,
        graphql_field.subscribe,
        graphql_field.description,
        graphql_field.deprecation_reason,
        graphql_field.extensions.copy() if graphql_field.extensions else None,
    )


def copy_field_type(new_types, field_type):
    if isinstance(field_type, GraphQLList):
        return GraphQLList(copy_field_type(new_types, field_type.of_type))

    if isinstance(field_type, GraphQLNonNull):
        return GraphQLNonNull(copy_field_type(new_types, field_type.of_type))

    if field_type == GraphQLBoolean:
        return GraphQLBoolean
    if field_type == GraphQLString:
        return GraphQLString
    if field_type == GraphQLFloat:
        return GraphQLFloat
    if field_type == GraphQLID:
        return GraphQLID
    if field_type == GraphQLInt:
        return GraphQLInt

    if isinstance(
        field_type,
        (
            GraphQLEnumType,
            GraphQLObjectType,
            GraphQLInterfaceType,
            GraphQLScalarType,
            GraphQLUnionType,
        ),
    ):
        return new_types[field_type.name]

    raise TypeError(f"Can't copy field of unknown type: '{repr(field_type)}'.")


def copy_arguments(
    new_types, field_args, field_exclude_args: Optional[List[str]] = None
):
    if field_args == {}:
        return {}

    args_to_exclude = field_exclude_args if field_exclude_args else []
    return {
        arg_name: copy_argument(new_types=new_types, arg=arg)
        for arg_name, arg in field_args.items()
        if arg_name not in args_to_exclude
    }


def copy_argument(new_types, arg) -> GraphQLArgument:
    return GraphQLArgument(
        copy_argument_type(new_types, arg.type),
        default_value=arg.default_value,
        description=arg.description,
        deprecation_reason=arg.deprecation_reason,
        out_name=arg.out_name,
    )


def copy_argument_type(new_types, arg):
    if isinstance(arg, GraphQLList):
        return GraphQLList(copy_argument_type(new_types, arg.of_type))

    if isinstance(arg, GraphQLNonNull):
        return GraphQLNonNull(copy_argument_type(new_types, arg.of_type))

    if arg == GraphQLBoolean:
        return GraphQLBoolean
    if arg == GraphQLString:
        return GraphQLString
    if arg == GraphQLFloat:
        return GraphQLFloat
    if arg == GraphQLID:
        return GraphQLID
    if arg == GraphQLInt:
        return GraphQLInt

    if isinstance(arg, (GraphQLEnumType, GraphQLInputObjectType, GraphQLScalarType)):
        return new_types[arg.name]

    raise TypeError(f"Can't copy argument of unknown type '{repr(arg)}'.")


def copy_input(
    new_types, graphql_type, object_exclude_fields: Optional[List[str]] = None
):
    def thunk():
        fields_to_exclude = object_exclude_fields if object_exclude_fields else []
        return {
            field_name: copy_input_field(new_types=new_types, field=field)
            for field_name, field in graphql_type.fields.items()
            if field_name not in fields_to_exclude
        }

    return GraphQLInputObjectType(
        graphql_type.name,
        thunk,
    )


def copy_input_field(new_types, field) -> GraphQLInputField:
    return GraphQLInputField(
        copy_input_field_type(new_types, field.type),
        default_value=field.default_value,
        description=field.description,
        deprecation_reason=field.deprecation_reason,
        out_name=field.out_name,
    )


def copy_input_field_type(new_types, field_type):
    if isinstance(field_type, GraphQLList):
        return GraphQLList(copy_input_field_type(new_types, field_type.of_type))

    if isinstance(field_type, GraphQLNonNull):
        return GraphQLNonNull(copy_input_field_type(new_types, field_type.of_type))

    if field_type == GraphQLBoolean:
        return GraphQLBoolean
    if field_type == GraphQLString:
        return GraphQLString
    if field_type == GraphQLFloat:
        return GraphQLFloat
    if field_type == GraphQLID:
        return GraphQLID
    if field_type == GraphQLInt:
        return GraphQLInt

    if isinstance(field_type, GraphQLNamedType):
        return new_types[field_type.name]

    raise TypeError(f"Can't copy input field of unknown type '{repr(field_type)}'.")


def copy_scalar(scalar):
    return GraphQLScalarType(
        name=scalar.name,
        serialize=scalar.serialize,
        parse_value=scalar.parse_value,
        parse_literal=scalar.parse_literal,
        description=scalar.description,
        specified_by_url=scalar.specified_by_url,
        extensions=scalar.extensions,
        ast_node=scalar.ast_node,
        extension_ast_nodes=scalar.extension_ast_nodes,
    )


def copy_interface(
    new_types: dict,
    interface_type: GraphQLInterfaceType,
    object_exclude_fields: Optional[List[str]] = None,
    object_exclude_args: Optional[Dict[str, List[str]]] = None,
) -> GraphQLInterfaceType:
    def fields_thunk():
        fields_to_exclude = object_exclude_fields if object_exclude_fields else []
        args_to_exclude = object_exclude_args if object_exclude_args else {}
        return {
            field_name: copy_field(new_types, field, args_to_exclude.get(field_name))
            for field_name, field in interface_type.fields.items()
            if field_name not in fields_to_exclude
        }

    def interfaces_thunk():
        return [new_types[i.name] for i in interface_type.interfaces]

    return GraphQLInterfaceType(
        name=interface_type.name,
        fields=fields_thunk,
        interfaces=interfaces_thunk,
    )


def copy_union(
    new_types: dict,
    union_type: GraphQLUnionType,
    exclude_types: Optional[List[str]] = None,
) -> GraphQLUnionType:
    def thunk():
        types_to_exclude = exclude_types if exclude_types else []
        return tuple(
            new_types[subtype.name]
            for subtype in union_type.types
            if subtype.name not in types_to_exclude
        )

    return GraphQLUnionType(name=union_type.name, types=thunk)


def copy_directives(
    new_types: dict,
    directives: Tuple[GraphQLDirective, ...],
    exclude_directives: Optional[List[str]] = None,
    exclude_directives_args: Optional[Dict[str, List[str]]] = None,
) -> Tuple[GraphQLDirective, ...]:
    exclude_directives = exclude_directives if exclude_directives else []
    exclude_directives_args = exclude_directives_args if exclude_directives_args else {}
    return tuple(
        copy_directive(
            new_types,
            directive,
            directive_exclude_args=exclude_directives_args.get(directive.name),
        )
        for directive in directives
        if directive.name not in exclude_directives
    )


def copy_directive(
    new_types: dict,
    directive: GraphQLDirective,
    directive_exclude_args: Optional[List[str]] = None,
) -> GraphQLDirective:
    return GraphQLDirective(
        name=directive.name,
        locations=directive.locations,
        args=copy_arguments(
            new_types, directive.args, field_exclude_args=directive_exclude_args
        ),
        is_repeatable=directive.is_repeatable,
        description=directive.description,
        extensions=directive.extensions.copy() if directive.extensions else {},
    )
