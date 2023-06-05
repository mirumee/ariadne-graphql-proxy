from itertools import chain
from typing import Optional, Union, cast

from graphql import (
    GraphQLArgument,
    GraphQLArgumentMap,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLEnumValueMap,
    GraphQLField,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInputType,
    GraphQLInterfaceType,
    GraphQLNamedType,
    GraphQLObjectType,
    GraphQLOutputType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLType,
    GraphQLUnionType,
    GraphQLWrappingType,
)

# Todo: https://github.com/graphql-python/graphql-core/pull/195
from graphql.type.definition import GraphQLInputFieldOutType

from .copy import (
    copy_argument,
    copy_argument_type,
    copy_arguments,
    copy_field,
    copy_field_type,
    copy_input_field,
    copy_input_field_type,
    copy_schema_type,
)
from .standard_types import STANDARD_TYPES


def merge_schemas(schema1: GraphQLSchema, schema2: GraphQLSchema) -> GraphQLSchema:
    merged_types = merge_type_maps(schema1.type_map, schema2.type_map)

    query_type = None
    if schema1.query_type:
        query_type = merged_types[schema1.query_type.name]
    elif schema2.query_type:
        query_type = merged_types[schema2.query_type.name]

    mutation_type = None
    if schema1.mutation_type:
        mutation_type = merged_types[schema1.mutation_type.name]
    elif schema2.mutation_type:
        mutation_type = merged_types[schema2.mutation_type.name]

    return GraphQLSchema(
        query=query_type, mutation=mutation_type, types=merged_types.values()
    )


def merge_type_maps(type_map1: dict, type_map2: dict) -> dict:
    merged_types: dict = {}
    for type_name in set(type_map1) | set(type_map2):
        if type_name in STANDARD_TYPES:
            continue

        type1 = type_map1.get(type_name)
        type2 = type_map2.get(type_name)

        if type1 is None or type2 is None:
            type_ = copy_schema_type(
                new_types=merged_types, graphql_type=type1 or type2
            )
        else:
            type_ = merge_types(merged_types=merged_types, type1=type1, type2=type2)

        if type_:
            merged_types[type_name] = type_

    return merged_types


def merge_types(
    merged_types: dict, type1: GraphQLType, type2: GraphQLType
) -> Optional[GraphQLType]:
    if isinstance(type1, GraphQLEnumType) and isinstance(type2, GraphQLEnumType):
        return merge_enums(enum1=type1, enum2=type2)

    if isinstance(type1, GraphQLObjectType) and isinstance(type2, GraphQLObjectType):
        return merge_objects(merged_types=merged_types, object1=type1, object2=type2)

    if isinstance(type1, GraphQLInputObjectType) and isinstance(
        type2, GraphQLInputObjectType
    ):
        return merge_inputs(merged_types=merged_types, input1=type1, input2=type2)

    if isinstance(type1, GraphQLScalarType) and isinstance(type2, GraphQLScalarType):
        return merge_scalars(type1, type2)

    if isinstance(type1, GraphQLInterfaceType) and isinstance(
        type2, GraphQLInterfaceType
    ):
        return merge_interfaces(
            merged_types=merged_types, interface1=type1, interface2=type2
        )

    if isinstance(type1, GraphQLUnionType) and isinstance(type2, GraphQLUnionType):
        return merge_unions(merged_types=merged_types, union1=type1, union2=type2)

    return None


def merge_enums(enum1: GraphQLEnumType, enum2: GraphQLEnumType) -> GraphQLEnumType:
    if (
        enum1.description
        and enum2.description
        and enum1.description != enum2.description
    ):
        raise TypeError(
            f"{enum1.name} descriptions don't match: "
            f"{repr(enum1.description)} != {repr(enum2.description)}"
        )

    values = enum1.values.copy()
    values.update(**enum2.values.copy())
    extensions = enum1.extensions.copy()
    extensions.update(**enum2.extensions.copy())

    return GraphQLEnumType(
        name=enum1.name,
        values=merge_enums_values(enum1, enum2),
        description=enum1.description or enum2.description,
        extensions=extensions,
    )


def merge_enums_values(
    enum1: GraphQLEnumType, enum2: GraphQLEnumType
) -> GraphQLEnumValueMap:
    merged_values: GraphQLEnumValueMap = {}

    for value_name in set(enum1.values) | set(enum2.values):
        value1 = enum1.values.get(value_name)
        value2 = enum2.values.get(value_name)

        if value1 is None or value2 is None:
            value = cast(GraphQLEnumValue, value1 or value2)
            merged_values[value_name] = GraphQLEnumValue(
                value=value.value,
                description=value.description,
                deprecation_reason=value.deprecation_reason,
                extensions=value.extensions,
                ast_node=value.ast_node,
            )
        else:
            if value1.value and value2.value and value1.value != value2.value:
                raise TypeError(
                    f"{enum1.name}.{value_name} values don't match: "
                    f"{repr(value1.value)} != {repr(value2.value)}"
                )

            if (
                value1.description
                and value2.description
                and value1.description != value2.description
            ):
                raise TypeError(
                    f"{enum1.name}.{value_name} descriptions don't match: "
                    f"{repr(value1.description)} != {repr(value2.description)}"
                )

            if (
                value1.deprecation_reason
                and value2.deprecation_reason
                and value1.deprecation_reason != value2.deprecation_reason
            ):
                raise TypeError(
                    f"{enum1.name}.{value_name} deprecation reasons don't match: "
                    f"{repr(value1.deprecation_reason)} != "
                    f"{repr(value2.deprecation_reason)}"
                )

            if (
                value1.ast_node
                and value2.ast_node
                and value1.ast_node != value2.ast_node
            ):
                raise TypeError(
                    f"{enum1.name}.{value_name} ast nodes don't match: "
                    f"{repr(value1.ast_node)} != {repr(value2.ast_node)}"
                )

            extensions = value1.extensions.copy()
            extensions.update(**value2.extensions.copy())

            merged_values[value_name] = GraphQLEnumValue(
                value=value1.value or value2.value,
                description=value1.description or value2.description,
                deprecation_reason=(
                    value1.deprecation_reason or value2.deprecation_reason
                ),
                extensions=extensions,
                ast_node=value1.ast_node or value2.ast_node,
            )

    return merged_values


def merge_objects(
    merged_types: dict, object1: GraphQLObjectType, object2: GraphQLObjectType
) -> GraphQLObjectType:
    if (
        object1.description
        and object2.description
        and object1.description != object2.description
    ):
        raise TypeError(
            f"{object1.name} descriptions don't match: "
            f"{repr(object1.description)} != {repr(object2.description)}"
        )

    def fields_thunk():
        merged_fields = {}
        for field_name in set(object1.fields.keys()) | set(object2.fields.keys()):
            field1 = object1.fields.get(field_name)
            field2 = object2.fields.get(field_name)
            if field1 is None or field2 is None:
                merged_fields[field_name] = copy_field(
                    new_types=merged_types, graphql_field=field1 or field2
                )
            else:
                merged_fields[field_name] = merge_fields(
                    merged_types=merged_types,
                    type_name=object1.name,
                    field_name=field_name,
                    field1=field1,
                    field2=field2,
                )
        return merged_fields

    def interfaces_thunk():
        interfaces_names = {
            i.name for i in chain(object1.interfaces, object2.interfaces)
        }
        return [merged_types[name] for name in interfaces_names]

    return GraphQLObjectType(
        name=object1.name,
        fields=fields_thunk,
        interfaces=interfaces_thunk,
        description=object1.description or object2.description,
    )


def merge_fields(
    merged_types: dict,
    type_name: str,
    field_name: str,
    field1: GraphQLField,
    field2: GraphQLField,
) -> GraphQLField:
    if not compare_types(field1.type, field2.type):
        raise TypeError(
            f"{type_name}.{field_name} type mismatch: {field1.type} != {field2.type}"
        )

    extensions = field1.extensions.copy()
    extensions.update(**field2.extensions.copy())

    if (
        field1.description
        and field2.description
        and field1.description != field2.description
    ):
        raise TypeError(
            f"{type_name}.{field_name} descriptions don't match: "
            f"{repr(field1.description)} != {repr(field2.description)}"
        )

    if (
        field1.deprecation_reason
        and field2.deprecation_reason
        and field1.deprecation_reason != field2.deprecation_reason
    ):
        raise TypeError(
            f"{type_name}.{field_name} deprecation reasons don't match: "
            f"{repr(field1.deprecation_reason)} != {repr(field2.deprecation_reason)}"
        )

    if not field1.args and not field2.args:
        args = None
    elif not field1.args or not field2.args:
        args = copy_arguments(
            new_types=merged_types, field_args=field1.args or field2.args
        )
    else:
        args = merge_args(
            merged_types=merged_types, args1=field1.args, args2=field2.args
        )

    return GraphQLField(
        description=field1.description or field2.description,
        deprecation_reason=field1.deprecation_reason or field2.deprecation_reason,
        type_=copy_field_type(new_types=merged_types, field_type=field1.type),
        args=args,
        extensions=extensions,
    )


def compare_types(
    type1: Union[GraphQLOutputType, GraphQLInputType],
    type2: Union[GraphQLOutputType, GraphQLInputType],
) -> bool:
    if isinstance(type1, GraphQLNamedType) and isinstance(type2, GraphQLNamedType):
        return type1.name == type2.name

    if isinstance(type1, GraphQLWrappingType) and isinstance(
        type2, GraphQLWrappingType
    ):
        return compare_types(type1.of_type, type2.of_type)

    return False


def merge_args(
    merged_types: dict, args1: GraphQLArgumentMap, args2: GraphQLArgumentMap
) -> GraphQLArgumentMap:
    merged_args = {}
    for arg_name in set(args1.keys()) | set(args2.keys()):
        arg1 = args1.get(arg_name)
        arg2 = args2.get(arg_name)

        if arg1 and arg2:
            if (
                arg1.default_value
                and arg2.default_value
                and arg1.default_value != arg2.default_value
            ):
                raise TypeError(
                    f"{arg_name} default values don't match: "
                    f"{repr(arg1.default_value)} != {repr(arg2.default_value)}"
                )

            if (
                arg1.description
                and arg2.description
                and arg1.description != arg2.description
            ):
                raise TypeError(
                    f"{arg_name} descriptions don't match: "
                    f"{repr(arg1.description)} != {repr(arg2.description)}"
                )

            if (
                arg1.deprecation_reason
                and arg2.deprecation_reason
                and arg1.deprecation_reason != arg2.deprecation_reason
            ):
                raise TypeError(
                    f"{arg_name} deprecation reasons don't match: "
                    f"{repr(arg1.deprecation_reason)} != "
                    f"{repr(arg2.deprecation_reason)}"
                )

            if arg1.out_name and arg2.out_name and arg1.out_name != arg2.out_name:
                raise TypeError(
                    f"{arg_name} out names don't match: "
                    f"{repr(arg1.out_name)} != {repr(arg2.out_name)}"
                )

            if not compare_types(arg1.type, arg2.type):
                raise TypeError(f"Argument type mismatch: {arg1.type} != {arg2.type}")

            merged_args[arg_name] = GraphQLArgument(
                copy_argument_type(merged_types, arg1.type),
                default_value=arg1.default_value or arg2.default_value,
                description=arg1.description or arg2.description,
                deprecation_reason=arg1.deprecation_reason or arg2.deprecation_reason,
                out_name=arg1.out_name or arg2.out_name,
            )
        else:
            merged_args[arg_name] = copy_argument(
                new_types=merged_types,
                arg=arg1 or arg2,
            )

    return merged_args


def merge_inputs(
    merged_types: dict,
    input1: GraphQLInputObjectType,
    input2: GraphQLInputObjectType,
) -> GraphQLInputObjectType:
    if (
        input1.description
        and input2.description
        and input1.description != input2.description
    ):
        raise TypeError(
            f"{input1.name} descriptions don't match: "
            f"{repr(input1.description)} != {repr(input2.description)}"
        )

    out_type_1 = get_input_custom_out_type(input1)
    out_type_2 = get_input_custom_out_type(input2)

    if out_type_1 and out_type_2 and out_type_1 != out_type_2:
        raise TypeError(
            f"{input1.name} out types don't match: "
            f"{repr(out_type_1)} != {repr(out_type_2)}"
        )

    def thunk():
        merged_fields = {}
        for field_name in set(input1.fields.keys()) | set(input2.fields.keys()):
            field1 = input1.fields.get(field_name)
            field2 = input2.fields.get(field_name)

            if field1 is None or field2 is None:
                merged_fields[field_name] = copy_input_field(
                    new_types=merged_types, field=field1 or field2
                )
            else:
                merged_fields[field_name] = merge_input_fields(
                    merged_types=merged_types,
                    type_name=input1.name,
                    field_name=field_name,
                    field1=field1,
                    field2=field2,
                )
        return merged_fields

    return GraphQLInputObjectType(
        name=input1.name,
        fields=thunk,
        description=input1.description or input2.description,
        out_type=out_type_1 or out_type_2,
    )


def get_input_custom_out_type(
    input_type: GraphQLInputObjectType,
) -> Optional[GraphQLInputFieldOutType]:
    if input_type.out_type is None:
        return None
    if input_type.out_type is GraphQLInputObjectType.out_type:
        return None

    return input_type.out_type


def merge_input_fields(
    merged_types: dict,
    type_name: str,
    field_name: str,
    field1: GraphQLInputField,
    field2: GraphQLInputField,
) -> GraphQLInputField:
    if not compare_types(field1.type, field2.type):
        raise TypeError(
            f"Input field types don't match: {field1.type} != {field2.type}"
        )

    if (
        field1.default_value
        and field2.default_value
        and field1.default_value != field2.default_value
    ):
        raise TypeError(
            "Input field default values don't match: "
            f"{field1.default_value} != {field2.default_value}"
        )

    if (
        field1.description
        and field2.description
        and field1.description != field2.description
    ):
        raise TypeError(
            f"{type_name}.{field_name} descriptions don't match: "
            f"{repr(field1.description)} != {repr(field2.description)}"
        )

    if (
        field1.deprecation_reason
        and field2.deprecation_reason
        and field1.deprecation_reason != field2.deprecation_reason
    ):
        raise TypeError(
            f"{type_name}.{field_name} deprecation reasons don't match: "
            f"{repr(field1.deprecation_reason)} != {repr(field2.deprecation_reason)}"
        )

    if field1.out_name and field2.out_name and field1.out_name != field2.out_name:
        raise TypeError(
            f"{type_name}.{field_name} out names don't match: "
            f"{repr(field1.out_name)} != {repr(field2.out_name)}"
        )

    return GraphQLInputField(
        copy_input_field_type(new_types=merged_types, field_type=field1.type),
        default_value=field1.default_value or field2.default_value,
        description=field1.description or field2.description,
        deprecation_reason=field1.deprecation_reason or field2.deprecation_reason,
        out_name=field1.out_name or field2.out_name,
    )


def merge_scalars(
    scalar1: GraphQLScalarType, scalar2: GraphQLScalarType
) -> GraphQLScalarType:
    if (
        scalar1.description
        and scalar2.description
        and scalar1.description != scalar2.description
    ):
        raise TypeError(
            f"{scalar1.name} descriptions don't match: "
            f"{repr(scalar1.description)} != {repr(scalar2.description)}"
        )

    if (
        scalar1.specified_by_url
        and scalar2.specified_by_url
        and scalar1.specified_by_url != scalar2.specified_by_url
    ):
        raise TypeError(
            f"{scalar1.name} specified_by_urls don't match: "
            f"{repr(scalar1.specified_by_url)} != {repr(scalar2.specified_by_url)}"
        )

    extensions = scalar1.extensions.copy()
    extensions.update(**scalar2.extensions.copy())

    return GraphQLScalarType(
        name=scalar1.name,
        description=scalar1.description or scalar2.description,
        specified_by_url=scalar1.specified_by_url or scalar2.specified_by_url,
        extensions=extensions,
        ast_node=scalar1.ast_node,
        extension_ast_nodes=scalar1.extension_ast_nodes,
    )


def merge_interfaces(
    merged_types: dict,
    interface1: GraphQLInterfaceType,
    interface2: GraphQLInterfaceType,
) -> GraphQLInterfaceType:
    if (
        interface1.description
        and interface2.description
        and interface1.description != interface2.description
    ):
        raise TypeError(
            f"{interface1.name} descriptions don't match: "
            f"{repr(interface1.description)} != {repr(interface2.description)}"
        )

    def fields_thunk():
        merged_fields = {}
        for field_name in set(interface1.fields.keys()) | set(interface2.fields.keys()):
            field1 = interface1.fields.get(field_name)
            field2 = interface2.fields.get(field_name)
            if field1 is None or field2 is None:
                merged_fields[field_name] = copy_field(
                    new_types=merged_types, graphql_field=field1 or field2
                )
            else:
                merged_fields[field_name] = merge_fields(
                    merged_types=merged_types,
                    type_name=interface1.name,
                    field_name=field_name,
                    field1=field1,
                    field2=field2,
                )
        return merged_fields

    def interfaces_thunk():
        interfaces_names = {
            i.name for i in chain(interface1.interfaces, interface2.interfaces)
        }
        return [merged_types[name] for name in interfaces_names]

    return GraphQLInterfaceType(
        name=interface1.name,
        fields=fields_thunk,
        interfaces=interfaces_thunk,
        description=interface1.description or interface2.description,
    )


def merge_unions(
    merged_types: dict, union1: GraphQLUnionType, union2: GraphQLUnionType
) -> GraphQLUnionType:
    if (
        union1.description
        and union2.description
        and union1.description != union2.description
    ):
        raise TypeError(
            f"{union1.name} descriptions don't match: "
            f"{repr(union1.description)} != {repr(union2.description)}"
        )

    def thunk():
        names = {t.name for t in chain(union1.types, union2.types)}
        return tuple(merged_types[subtype_name] for subtype_name in names)

    return GraphQLUnionType(
        name=union1.name,
        types=thunk,
        description=union1.description or union2.description,
    )
