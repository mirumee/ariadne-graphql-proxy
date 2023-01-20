from itertools import chain
from typing import Optional, Union

from graphql import (
    GraphQLArgumentMap,
    GraphQLEnumType,
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

from .copy_schema import (
    copy_argument,
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
    merged_types = {}
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
    if enum1.description != enum2.description:
        raise Exception

    values = enum1.values.copy()
    values.update(**enum2.values.copy())
    extensions = enum1.extensions.copy()
    extensions.update(**enum2.extensions.copy())

    return GraphQLEnumType(
        name=enum1.name,
        values=values,
        description=enum1.description,
        extensions=extensions,
    )


def merge_objects(
    merged_types: dict, object1: GraphQLObjectType, object2: GraphQLObjectType
) -> GraphQLObjectType:
    def thunk():
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
                    merged_types=merged_types, field1=field1, field2=field2
                )
        return merged_fields

    return GraphQLObjectType(
        object1.name,
        thunk,
    )


def merge_fields(
    merged_types: dict, field1: GraphQLField, field2: GraphQLField
) -> GraphQLField:
    if not compare_types(field1.type, field2.type):
        raise Exception(f"Field types mismatch: {field1.type} =/= {field2.type}")

    extensions = field1.extensions.copy()
    extensions.update(**field2.extensions.copy())

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

        if arg1 and arg2 and compare_types(arg1.type, arg2.type):
            raise Exception(f"Argument type mismatch: {arg1.type} =/= {arg2.type}")

        merged_args[arg_name] = copy_argument(new_types=merged_types, arg=arg1 or arg2)

    return merged_args


def merge_inputs(
    merged_types: dict,
    input1: GraphQLInputObjectType,
    input2: GraphQLInputObjectType,
) -> GraphQLInputObjectType:
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
                    merged_types=merged_types, field1=field1, field2=field2
                )
        return merged_fields

    return GraphQLInputObjectType(
        input1.name,
        thunk,
    )


def merge_input_fields(
    merged_types: dict, field1: GraphQLInputField, field2: GraphQLInputField
) -> GraphQLInputField:
    if not compare_types(field1.type, field2.type):
        raise Exception(f"Input field types mismatch: {field1.type} =/= {field2.type}")
    if field1.default_value != field2.default_value:
        raise Exception(
            "Input field default value mismatch: "
            f"{field1.default_value} =/= {field2.default_value}"
        )
    if field1.description != field2.description:
        raise Exception(
            "Input field description mismatch: "
            f"{field1.description} =/= {field2.description}"
        )
    if field1.deprecation_reason != field2.deprecation_reason:
        raise Exception(
            "Input field deprecation reason mismatch: "
            f"{field1.deprecation_reason} =/= {field2.deprecation_reason}"
        )
    if field1.out_name != field2.out_name:
        raise Exception(
            f"Input field out name mismatch: {field1.out_name} =/= {field2.out_name}"
        )

    return GraphQLInputField(
        copy_input_field_type(new_types=merged_types, field_type=field1.type),
        default_value=field1.default_value,
        description=field1.description,
        deprecation_reason=field1.deprecation_reason,
        out_name=field1.out_name,
    )


def merge_scalars(
    type1: GraphQLScalarType, type2: GraphQLScalarType
) -> GraphQLScalarType:
    if type1.description != type2.description:
        raise Exception(
            "Scalar description mismatch : "
            f"{type1.description} =/= {type2.description}"
        )
    if type1.specified_by_url != type2.specified_by_url:
        raise Exception(
            "Scalar specified_by_url mismatch : "
            f"{type1.specified_by_url} =/= {type2.specified_by_url}"
        )

    extensions = type1.extensions.copy()
    extensions.update(**type2.extensions.copy())

    return GraphQLScalarType(
        name=type1.name,
        description=type1.description,
        specified_by_url=type1.specified_by_url,
        extensions=extensions,
        ast_node=type1.ast_node,
        extension_ast_nodes=type1.extension_ast_nodes,
    )


def merge_interfaces(
    merged_types: dict,
    interface1: GraphQLInterfaceType,
    interface2: GraphQLInterfaceType,
) -> GraphQLInterfaceType:
    def thunk():
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
                    merged_types=merged_types, field1=field1, field2=field2
                )
        return merged_fields

    return GraphQLInterfaceType(
        interface1.name,
        thunk,
    )


def merge_unions(
    merged_types: dict, union1: GraphQLUnionType, union2: GraphQLUnionType
) -> GraphQLUnionType:
    def thunk():
        names = {t.name for t in chain(union1.types, union2.types)}
        return tuple(merged_types[subtype_name] for subtype_name in names)

    return GraphQLUnionType(name=union1.name, types=thunk)
