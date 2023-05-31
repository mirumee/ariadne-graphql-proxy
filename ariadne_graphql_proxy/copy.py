from typing import Dict, List, Optional, Tuple

from graphql import (
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

from .standard_types import STANDARD_TYPES


def copy_schema(
    schema: GraphQLSchema,
    *,
    exclude_types: Optional[List[str]] = None,
    exclude_args: Optional[Dict[str, Dict[str, List[str]]]] = None,
    exclude_fields: Optional[Dict[str, List[str]]] = None,
    exclude_directives: Optional[List[str]] = None,
    exclude_directives_args: Optional[Dict[str, List[str]]] = None,
) -> GraphQLSchema:
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
    if schema.mutation_type:
        mutation_type = new_types[schema.mutation_type.name]

    new_schema = GraphQLSchema(
        query=query_type,
        mutation=mutation_type,
        types=new_types.values(),
        directives=copy_directives(
            new_types,
            schema.directives,
            exclude_directives=exclude_directives,
            exclude_directives_args=exclude_directives_args,
        ),
    )
    assert_valid_schema(new_schema)
    return new_schema


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
