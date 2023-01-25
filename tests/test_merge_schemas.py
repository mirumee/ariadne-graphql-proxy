import pytest
from graphql import (
    GraphQLArgument,
    GraphQLEnumType,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLFloat,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInt,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLString,
    GraphQLUnionType,
    build_ast_schema,
    parse,
)

from ariadne_graphql_proxy.merge_schemas import (
    merge_args,
    merge_enums,
    merge_fields,
    merge_input_fields,
    merge_inputs,
    merge_interfaces,
    merge_objects,
    merge_scalars,
    merge_schemas,
    merge_type_maps,
    merge_types,
    merge_unions,
)


@pytest.mark.parametrize(
    "type1_str, type2_str, type1_name, type2_name",
    [
        (
            "type TestTypeA { fieldA: String! }",
            "type TestTypeB { fieldB: String! }",
            "TestTypeA",
            "TestTypeB",
        ),
        (
            "enum TestEnumA { VALA }",
            "enum TestEnumB { VALB }",
            "TestEnumA",
            "TestEnumB",
        ),
        (
            "interface TestInterfaceA { fieldA: String! }",
            "interface TestInterfaceB { fieldB: String! }",
            "TestInterfaceA",
            "TestInterfaceB",
        ),
        (
            "input TestInputA { fieldA: String! }",
            "input TestInputB{ fieldB: String! }",
            "TestInputA",
            "TestInputB",
        ),
        (
            """
            type TestTypeA1 { fieldA1: String! }
            type TestTypeA2 { fieldA1: String! }
            union TestUnionA = TestTypeA1 | TestTypeA2
            """,
            """
            type TestTypeB1 { fieldB1: String! }
            type TestTypeB2 { fieldB1: String! }
            union TestUnionB = TestTypeB1 | TestTypeB2
            """,
            "TestUnionA",
            "TestUnionB",
        ),
    ],
)
def test_merge_schemas_returns_schema_with_types_from_both_schemas(
    gql, type1_str, type2_str, type1_name, type2_name
):
    schema_str = gql(
        """
        schema { query: Query }
        type Query { _skip: Int! }
        """
    )
    schema1 = build_ast_schema(parse(schema_str + type1_str))
    schema2 = build_ast_schema(parse(schema_str + type2_str))

    merged_schema = merge_schemas(schema1, schema2)

    assert isinstance(merged_schema, GraphQLSchema)
    type1 = merged_schema.type_map[type1_name]
    assert type1
    assert type1 is not schema1.type_map[type1_name]
    type2 = merged_schema.type_map[type2_name]
    assert type2
    assert type2 is not schema2.type_map[type2_name]


@pytest.mark.parametrize(
    "type_str, type_name",
    [
        ("type TestTypeA { fieldA: String! }", "TestTypeA"),
        ("enum TestEnumA { VALA }", "TestEnumA"),
        ("interface TestInterfaceA { fieldA: String! }", "TestInterfaceA"),
        ("input TestInputA { fieldA: String! }", "TestInputA"),
        (
            """
            type TestTypeA1 { fieldA1: String! }
            type TestTypeA2 { fieldA1: String! }
            union TestUnionA = TestTypeA1 | TestTypeA2
            """,
            "TestUnionA",
        ),
    ],
)
def test_merge_schemas_returns_schema_with_not_duplicated_type(
    gql, type_str, type_name
):
    schema_str = gql(
        """
        schema { query: Query }
        type Query { _skip: Int! }
        """
    )
    schema1 = build_ast_schema(parse(schema_str + type_str))
    schema2 = build_ast_schema(parse(schema_str + type_str))

    merged_schema = merge_schemas(schema1, schema2)

    assert isinstance(merged_schema, GraphQLSchema)
    type_ = merged_schema.type_map[type_name]
    assert type_
    assert type_ is not schema1.type_map[type_name]
    assert type_ is not schema2.type_map[type_name]


@pytest.mark.parametrize(
    "type1_str, type2_str, type_name",
    [
        (
            """
            type TestType {
                common: Int!
                fieldA: String!
            }
            """,
            """
            type TestType {
                common: Int!
                fieldB: String!
            }
            """,
            "TestType",
        ),
        (
            """
            interface TestInterface {
                common: Int!
                fieldA: String!
            }
            """,
            """
            interface TestInterface {
                common: Int!
                fieldB: String!
            }
            """,
            "TestInterface",
        ),
        (
            """
            input TestInput {
                common: Int!
                fieldA: String!
            }
            """,
            """
            input TestInput {
                common: Int!
                fieldB: String!
            }
            """,
            "TestInput",
        ),
    ],
)
def test_merge_schemas_returns_schema_with_type_with_merged_fields(
    gql, type1_str, type2_str, type_name
):
    schema_str = gql(
        """
        schema { query: Query }
        type Query { _skip: Int! }
        """
    )
    schema1 = build_ast_schema(parse(schema_str + type1_str))
    schema2 = build_ast_schema(parse(schema_str + type2_str))

    merged_schema = merge_schemas(schema1, schema2)

    assert isinstance(merged_schema, GraphQLSchema)
    common_field = merged_schema.type_map[type_name].fields["common"]
    assert common_field
    assert common_field is not schema1.type_map[type_name].fields["common"]
    assert common_field is not schema2.type_map[type_name].fields["common"]
    field_a = merged_schema.type_map[type_name].fields["fieldA"]
    assert field_a
    assert field_a is not schema1.type_map[type_name].fields["fieldA"]
    field_b = merged_schema.type_map[type_name].fields["fieldB"]
    assert field_b
    assert field_b is not schema2.type_map[type_name].fields["fieldB"]


def test_merge_schemas_returns_schema_with_enum_with_merged_values(gql):
    schema_str = gql(
        """
        schema { query: Query }
        type Query { _skip: Int! }
        """
    )
    enum1_str = gql(
        """
        enum TestEnum {
            COMMON
            VALA
        }
        """
    )
    enum2_str = gql(
        """
        enum TestEnum {
            COMMON
            VALB
        }
        """
    )
    schema1 = build_ast_schema(parse(schema_str + enum1_str))
    schema2 = build_ast_schema(parse(schema_str + enum2_str))

    merged_schema = merge_schemas(schema1, schema2)

    assert isinstance(merged_schema, GraphQLSchema)
    enum_type = merged_schema.type_map["TestEnum"]
    assert enum_type
    assert enum_type.values["COMMON"]
    assert enum_type.values["VALA"]
    assert enum_type.values["VALB"]


def test_merge_schemas_returns_schema_with_merged_union(gql):
    schema_str = gql(
        """
        schema { query: Query }
        type Query { _skip: Int! }
        type TestTypeCommon {
            common: String
        }
        """
    )
    union1_str = gql(
        """
        type TestTypeA {
            fieldA: String!
        }
        union TestUnion = TestTypeCommon | TestTypeA
        """
    )
    union2_str = gql(
        """
        type TestTypeB {
            fieldB: String!
        }
        union TestUnion = TestTypeCommon | TestTypeB
        """
    )
    schema1 = build_ast_schema(parse(schema_str + union1_str))
    schema2 = build_ast_schema(parse(schema_str + union2_str))

    merged_schema = merge_schemas(schema1, schema2)

    assert isinstance(merged_schema, GraphQLSchema)
    uniont_type = merged_schema.type_map["TestUnion"]
    assert uniont_type
    assert uniont_type is not schema1.type_map["TestUnion"]
    assert uniont_type is not schema2.type_map["TestUnion"]
    assert {t.name for t in uniont_type.types} == {
        "TestTypeCommon",
        "TestTypeA",
        "TestTypeB",
    }


def test_merge_schemas_returns_schema_with_merged_implemented_interfaces(gql):
    schema_str = gql(
        """
        schema { query: Query }
        type Query { _skip: Int! }
        """
    )
    interface1_str = gql(
        """
        interface TestInterfaceA { fieldA: String! }
        type TestType implements TestInterfaceA{
            fieldA: String!
        }
        """
    )
    interface2_str = gql(
        """
        interface TestInterfaceB { fieldB: String! }
        type TestType implements TestInterfaceB{
            fieldB: String!
        }
        """
    )
    schema1 = build_ast_schema(parse(schema_str + interface1_str))
    schema2 = build_ast_schema(parse(schema_str + interface2_str))

    merged_schema = merge_schemas(schema1, schema2)

    assert isinstance(merged_schema, GraphQLSchema)
    type_ = merged_schema.type_map["TestType"]
    assert type_
    assert type_ is not schema1.type_map["TestType"]
    assert type_ is not schema2.type_map["TestType"]
    assert {t.name for t in type_.interfaces} == {"TestInterfaceA", "TestInterfaceB"}


def test_merge_schemas_returns_schema_with_merged_arguments(gql):
    schema1_str = gql(
        """
        schema { query: Query }
        type Query {
            testQuery(argA: Int, argB: String): Float
        }
        """
    )
    schema2_str = gql(
        """
        schema { query: Query }
        type Query {
            testQuery(argA: Int, argC: Boolean): Float
        }
        """
    )
    schema1 = build_ast_schema(parse(schema1_str))
    schema2 = build_ast_schema(parse(schema2_str))

    merged_schema = merge_schemas(schema1, schema2)

    assert isinstance(merged_schema, GraphQLSchema)
    args = merged_schema.type_map["Query"].fields["testQuery"].args
    assert args
    assert args["argA"]
    assert args["argB"]
    assert args["argC"]


def test_merge_schemas_with_different_types_field_raises_exception(gql):
    schema1_str = gql(
        """
        schema { query: Query }
        type Query {
            testQuery: Float
        }
        """
    )
    schema2_str = gql(
        """
        schema { query: Query }
        type Query {
            testQuery: Int
        }
        """
    )
    schema1 = build_ast_schema(parse(schema1_str))
    schema2 = build_ast_schema(parse(schema2_str))

    with pytest.raises(TypeError):
        merge_schemas(schema1, schema2)


def test_merge_schemas_with_different_types_argument_raises_exception(gql):
    schema1_str = gql(
        """
        schema { query: Query }
        type Query {
            testQuery(arg: String): Int
        }
        """
    )
    schema2_str = gql(
        """
        schema { query: Query }
        type Query {
            testQuery(arg: Float): Int
        }
        """
    )
    schema1 = build_ast_schema(parse(schema1_str))
    schema2 = build_ast_schema(parse(schema2_str))

    with pytest.raises(TypeError):
        merge_schemas(schema1, schema2)


def test_merge_type_maps_calls_copy_schema_type_if_object_is_not_present_in_one_map(
    mocker,
):
    mocked_copy_schema_type = mocker.patch(
        "ariadne_graphql_proxy.merge_schemas.copy_schema_type"
    )
    type_ = GraphQLObjectType(
        name="TypeName",
        fields={"fieldA": GraphQLField(type_=GraphQLString)},
    )

    merge_type_maps(type_map1={"TypeName": type_}, type_map2={})

    assert mocked_copy_schema_type.called
    assert mocked_copy_schema_type.called_with(new_types={}, graphql_type=type_)


def test_merge_type_maps_calls_merge_types_if_objectt_is_present_in_both_maps(
    mocker,
):
    mocked_merge_types = mocker.patch("ariadne_graphql_proxy.merge_schemas.merge_types")
    type1 = GraphQLObjectType(
        name="TypeName",
        fields={"fieldA": GraphQLField(type_=GraphQLString)},
    )
    type2 = GraphQLObjectType(
        name="TypeName",
        fields={"fieldA": GraphQLField(type_=GraphQLString)},
    )
    merge_type_maps(type_map1={"TypeName": type1}, type_map2={"TypeName": type2})

    assert mocked_merge_types.called
    assert mocked_merge_types.called_with(merge_types={}, type1=type1, type2=type2)


@pytest.mark.parametrize(
    "type1, type2, method_name",
    [
        (
            GraphQLEnumType(
                name="EnumType",
                values={
                    "VAL1": GraphQLEnumValue(value="VAL1"),
                    "VAL2": GraphQLEnumValue(value="VAL2"),
                },
            ),
            GraphQLEnumType(
                name="EnumType",
                values={
                    "VAL1": GraphQLEnumValue(value="VAL1"),
                    "VAL3": GraphQLEnumValue(value="VAL3"),
                },
            ),
            "merge_enums",
        ),
        (
            GraphQLObjectType(
                name="TypeA", fields={"valA": GraphQLField(type_=GraphQLString)}
            ),
            GraphQLObjectType(
                name="TypeA", fields={"valB": GraphQLField(type_=GraphQLString)}
            ),
            "merge_objects",
        ),
        (
            GraphQLInputObjectType(
                name="TypeA", fields={"valA": GraphQLInputField(type_=GraphQLString)}
            ),
            GraphQLInputObjectType(
                name="TypeA", fields={"valB": GraphQLInputField(type_=GraphQLString)}
            ),
            "merge_inputs",
        ),
        (
            GraphQLScalarType(name="ScalarName"),
            GraphQLScalarType(name="ScalarName"),
            "merge_scalars",
        ),
        (
            GraphQLInterfaceType(
                name="TypeA", fields={"valA": GraphQLField(type_=GraphQLString)}
            ),
            GraphQLInterfaceType(
                name="TypeA", fields={"valB": GraphQLField(type_=GraphQLString)}
            ),
            "merge_interfaces",
        ),
        (
            GraphQLUnionType(name="UnionType", types=()),
            GraphQLUnionType(name="UnionType", types=()),
            "merge_unions",
        ),
    ],
)
def test_merge_types_calls_correct_merge_method(mocker, type1, type2, method_name):
    mocked_merge_method = mocker.patch(
        f"ariadne_graphql_proxy.merge_schemas.{method_name}"
    )

    merge_types(merged_types={}, type1=type1, type2=type2)

    assert mocked_merge_method.called


def test_merge_enums_returns_enum_with_values_from_both_enums():
    enum1 = GraphQLEnumType(
        name="EnumType",
        values={
            "VAL1": GraphQLEnumValue(value="VAL1"),
            "VAL2": GraphQLEnumValue(value="VAL2"),
        },
        extensions={"extension1": "1"},
    )
    enum2 = GraphQLEnumType(
        name="EnumType",
        values={
            "VAL1": GraphQLEnumValue(value="VAL1"),
            "VAL3": GraphQLEnumValue(value="VAL3"),
        },
        extensions={"extension2": "2"},
    )

    merged_enum = merge_enums(enum1=enum1, enum2=enum2)

    assert isinstance(merged_enum, GraphQLEnumType)
    assert merged_enum.values["VAL1"]
    assert merged_enum.values["VAL2"]
    assert merged_enum.values["VAL3"]
    assert merged_enum.extensions["extension1"]
    assert merged_enum.extensions["extension2"]


def test_merge_enums_raises_type_error_for_not_matching_descriptions():
    enum1 = GraphQLEnumType(
        name="EnumType",
        values={"VAL1": GraphQLEnumValue(value="VAL1")},
        description="desc2",
    )
    enum2 = GraphQLEnumType(
        name="EnumType",
        values={"VAL1": GraphQLEnumValue(value="VAL1")},
        description="desc1",
    )

    with pytest.raises(TypeError):
        merge_enums(enum1=enum1, enum2=enum2)


def test_merge_objects_returns_object_with_fields_from_both_objects():
    related_type = GraphQLObjectType(
        name="RelatedType", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    merged_related_type = GraphQLObjectType(
        name="RelatedType", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    object1 = GraphQLObjectType(
        name="TestType",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
            "fieldB": GraphQLField(type_=related_type),
        },
    )
    object2 = GraphQLObjectType(
        name="TestType",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
            "fieldC": GraphQLField(type_=GraphQLFloat),
        },
    )

    merged_object = merge_objects(
        merged_types={"RelatedType": merged_related_type},
        object1=object1,
        object2=object2,
    )

    assert isinstance(merged_object, GraphQLObjectType)
    assert merged_object.fields["fieldA"]
    assert merged_object.fields["fieldB"]
    assert merged_object.fields["fieldC"]


def test_merge_objects_returns_object_with_merged_implemented_interfaces():
    interface1 = GraphQLInterfaceType(
        name="TestInterface1", fields={"fieldA": GraphQLField(type_=GraphQLString)}
    )
    interface2 = GraphQLInterfaceType(
        name="TestInterface2", fields={"fieldA": GraphQLField(type_=GraphQLString)}
    )
    merged_interface1 = GraphQLInterfaceType(
        name="TestInterface1", fields={"fieldA": GraphQLField(type_=GraphQLString)}
    )
    merged_interface2 = GraphQLInterfaceType(
        name="TestInterface2", fields={"fieldA": GraphQLField(type_=GraphQLString)}
    )
    object1 = GraphQLObjectType(
        name="TestType",
        fields={"fieldA": GraphQLField(type_=GraphQLString)},
        interfaces=[interface1],
    )
    object2 = GraphQLObjectType(
        name="TestType",
        fields={"fieldA": GraphQLField(type_=GraphQLString)},
        interfaces=[interface2],
    )

    merged_object = merge_objects(
        merged_types={
            "TestInterface1": merged_interface1,
            "TestInterface2": merged_interface2,
        },
        object1=object1,
        object2=object2,
    )

    assert isinstance(merged_object, GraphQLObjectType)
    assert len(merged_object.interfaces) == 2
    assert {i.name for i in merged_object.interfaces} == {
        "TestInterface1",
        "TestInterface2",
    }


def test_merge_fields_returns_field_with_arguments_from_both_fields():
    field1 = GraphQLField(
        type_=GraphQLString,
        args={
            "arg1": GraphQLArgument(type_=GraphQLString),
            "arg2": GraphQLArgument(type_=GraphQLString),
        },
    )
    field2 = GraphQLField(
        type_=GraphQLString,
        args={
            "arg1": GraphQLArgument(type_=GraphQLString),
            "arg3": GraphQLArgument(type_=GraphQLString),
        },
    )

    merged_field = merge_fields(merged_types={}, field1=field1, field2=field2)

    assert isinstance(merged_field, GraphQLField)
    assert merged_field.args["arg1"]
    assert merged_field.args["arg2"]
    assert merged_field.args["arg3"]


def test_merge_fields_returns_field_with_copied_arguments_from_one_field():
    field1 = GraphQLField(
        type_=GraphQLString,
        args={
            "arg1": GraphQLArgument(type_=GraphQLString),
            "arg2": GraphQLArgument(type_=GraphQLString),
        },
    )
    field2 = GraphQLField(type_=GraphQLString)

    merged_field = merge_fields(merged_types={}, field1=field1, field2=field2)

    assert isinstance(merged_field, GraphQLField)
    assert merged_field.args["arg1"]
    assert merged_field.args["arg1"] is not field1.args["arg1"]
    assert merged_field.args["arg2"]
    assert merged_field.args["arg2"] is not field1.args["arg2"]


@pytest.mark.parametrize(
    "type1, type2",
    [
        (GraphQLString, GraphQLFloat),
        (GraphQLString, GraphQLList(GraphQLString)),
        (GraphQLInt, GraphQLNonNull(GraphQLInt)),
    ],
)
def test_merge_fields_raises_type_error_for_not_matching_types(type1, type2):
    field1 = GraphQLField(type_=type1)
    field2 = GraphQLField(type_=type2)

    with pytest.raises(TypeError):
        merge_fields(merged_types={}, field1=field1, field2=field2)


def test_merge_args_returns_dict_with_merged_args():
    arg1 = GraphQLArgument(type_=GraphQLString)
    duplicated_arg1 = GraphQLArgument(type_=GraphQLString)
    arg2 = GraphQLArgument(type_=GraphQLString)
    arg3 = GraphQLArgument(type_=GraphQLString)

    merged_args = merge_args(
        merged_types={},
        args1={"arg1": arg1, "arg2": arg2},
        args2={"arg1": duplicated_arg1, "arg3": arg3},
    )

    assert merged_args["arg1"]
    assert merged_args["arg1"] is not arg1
    assert merged_args["arg1"] is not duplicated_arg1
    assert merged_args["arg2"]
    assert merged_args["arg2"] is not arg2
    assert merged_args["arg3"]
    assert merged_args["arg3"] is not arg3


@pytest.mark.parametrize(
    "type1, type2",
    [
        (GraphQLString, GraphQLFloat),
        (GraphQLString, GraphQLList(GraphQLString)),
        (GraphQLInt, GraphQLNonNull(GraphQLInt)),
    ],
)
def test_merge_args_raises_type_error_for_not_matching_types(type1, type2):
    with pytest.raises(TypeError):
        merge_args(
            merged_types={},
            args1={"arg1": GraphQLArgument(type_=type1)},
            args2={"arg1": GraphQLArgument(type_=type2)},
        )


def test_merge_inputs_returns_input_with_fields_from_both_inputs():
    related_input = GraphQLInputObjectType(
        name="RelatedInput", fields={"val": GraphQLInputField(type_=GraphQLString)}
    )
    merged_related_input = GraphQLInputObjectType(
        name="RelatedInput", fields={"val": GraphQLInputField(type_=GraphQLString)}
    )
    input1 = GraphQLInputObjectType(
        name="TestInput",
        fields={
            "fieldA": GraphQLInputField(type_=GraphQLString),
            "fieldB": GraphQLInputField(type_=related_input),
        },
    )
    input2 = GraphQLInputObjectType(
        name="TestInput",
        fields={
            "fieldA": GraphQLInputField(type_=GraphQLString),
            "fieldC": GraphQLInputField(type_=GraphQLFloat),
        },
    )

    merged_input = merge_inputs(
        merged_types={"RelatedInput": merged_related_input},
        input1=input1,
        input2=input2,
    )

    assert isinstance(merged_input, GraphQLInputObjectType)
    assert merged_input.fields["fieldA"]
    assert merged_input.fields["fieldB"]
    assert merged_input.fields["fieldC"]


def test_merge_input_fields_returns_field():
    field1 = GraphQLInputField(
        type_=GraphQLFloat,
        default_value=2.5,
        description="desc",
        deprecation_reason="reason",
        out_name="out name",
    )
    field2 = GraphQLInputField(
        type_=GraphQLFloat,
        default_value=2.5,
        description="desc",
        deprecation_reason="reason",
        out_name="out name",
    )

    merged_field = merge_input_fields(merged_types={}, field1=field1, field2=field2)

    assert isinstance(merged_field, GraphQLInputField)
    assert merged_field is not field1
    assert merged_field is not field2
    assert merged_field.default_value == field1.default_value
    assert merged_field.description == field1.description
    assert merged_field.deprecation_reason == field1.deprecation_reason
    assert merged_field.out_name == field1.out_name


def test_merge_input_fields_raises_type_error_for_not_matching_types():
    field1 = GraphQLInputField(type_=GraphQLString)
    field2 = GraphQLInputField(type_=GraphQLFloat)

    with pytest.raises(TypeError):
        merge_input_fields(merged_types={}, field1=field1, field2=field2)


def test_merge_input_fields_raises_type_error_for_not_matching_default_value():
    field1 = GraphQLInputField(type_=GraphQLString, default_value="a")
    field2 = GraphQLInputField(type_=GraphQLString, default_value="b")

    with pytest.raises(TypeError):
        merge_input_fields(merged_types={}, field1=field1, field2=field2)


def test_merge_input_fields_raises_type_error_for_not_matching_description():
    field1 = GraphQLInputField(type_=GraphQLString, description="desc1")
    field2 = GraphQLInputField(type_=GraphQLString, description="desc2")

    with pytest.raises(TypeError):
        merge_input_fields(merged_types={}, field1=field1, field2=field2)


def test_merge_input_fields_raises_type_error_for_not_matching_deprecation_reason():
    field1 = GraphQLInputField(type_=GraphQLString, deprecation_reason="reason1")
    field2 = GraphQLInputField(type_=GraphQLString, deprecation_reason="reason2")

    with pytest.raises(TypeError):
        merge_input_fields(merged_types={}, field1=field1, field2=field2)


def test_merge_input_fields_raises_type_error_for_not_matching_out_name():
    field1 = GraphQLInputField(type_=GraphQLString, out_name="name1")
    field2 = GraphQLInputField(type_=GraphQLString, out_name="name2")

    with pytest.raises(TypeError):
        merge_input_fields(merged_types={}, field1=field1, field2=field2)


def test_merge_scalars_returns_merged_scalar():
    scalar1 = GraphQLScalarType(
        name="TestScalar", description="desc", specified_by_url="url"
    )
    scalar2 = GraphQLScalarType(
        name="TestScalar", description="desc", specified_by_url="url"
    )

    merged_scalar = merge_scalars(scalar1=scalar1, scalar2=scalar2)

    assert isinstance(merged_scalar, GraphQLScalarType)
    assert merged_scalar is not scalar1
    assert merged_scalar is not scalar2
    assert merged_scalar.name == scalar1.name
    assert merged_scalar.description == scalar1.description
    assert merged_scalar.specified_by_url == scalar1.specified_by_url


def test_merge_scalars_raises_type_error_for_not_matching_description():
    scalar1 = GraphQLScalarType(name="TestScalar", description="desc1")
    scalar2 = GraphQLScalarType(name="TestScalar", description="desc2")

    with pytest.raises(TypeError):
        merge_scalars(scalar1=scalar1, scalar2=scalar2)


def test_merge_scalars_raises_type_error_for_not_matching_specifed_by_url():
    scalar1 = GraphQLScalarType(name="TestScalar", specified_by_url="url1")
    scalar2 = GraphQLScalarType(name="TestScalar", specified_by_url="url2")

    with pytest.raises(TypeError):
        merge_scalars(scalar1=scalar1, scalar2=scalar2)


def test_merge_interfaces_returns_interface_with_fields_from_both_interfaces():
    related_type = GraphQLObjectType(
        name="RelatedType", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    merged_related_type = GraphQLObjectType(
        name="RelatedType", fields={"val": GraphQLField(type_=GraphQLString)}
    )
    interface1 = GraphQLInterfaceType(
        name="TestInterface",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
            "fieldB": GraphQLField(type_=related_type),
        },
    )
    interface2 = GraphQLInterfaceType(
        name="TestInput",
        fields={
            "fieldA": GraphQLField(type_=GraphQLString),
            "fieldC": GraphQLField(type_=GraphQLFloat),
        },
    )

    merged_interface = merge_interfaces(
        merged_types={"RelatedType": merged_related_type},
        interface1=interface1,
        interface2=interface2,
    )

    assert isinstance(merged_interface, GraphQLInterfaceType)
    assert merged_interface.fields["fieldA"]
    assert merged_interface.fields["fieldB"]
    assert merged_interface.fields["fieldC"]


def test_merge_interfaces_returns_interface_with_merged_implemented_interfaces():
    implemented_interface1 = GraphQLInterfaceType(
        name="TestInterface1", fields={"fieldA": GraphQLField(type_=GraphQLString)}
    )
    implemented_interface2 = GraphQLInterfaceType(
        name="TestInterface2", fields={"fieldA": GraphQLField(type_=GraphQLString)}
    )
    merged_implemented_interface1 = GraphQLInterfaceType(
        name="TestInterface1", fields={"fieldA": GraphQLField(type_=GraphQLString)}
    )
    merged_implemented_interface2 = GraphQLInterfaceType(
        name="TestInterface2", fields={"fieldA": GraphQLField(type_=GraphQLString)}
    )
    interface1 = GraphQLInterfaceType(
        name="TestInterface",
        fields={"fieldA": GraphQLField(type_=GraphQLString)},
        interfaces=[implemented_interface1],
    )
    interface2 = GraphQLInterfaceType(
        name="TestType",
        fields={"fieldA": GraphQLField(type_=GraphQLString)},
        interfaces=[implemented_interface2],
    )

    merged_interface = merge_interfaces(
        merged_types={
            "TestInterface1": merged_implemented_interface1,
            "TestInterface2": merged_implemented_interface2,
        },
        interface1=interface1,
        interface2=interface2,
    )

    assert isinstance(merged_interface, GraphQLInterfaceType)
    assert len(merged_interface.interfaces) == 2
    assert {i.name for i in merged_interface.interfaces} == {
        "TestInterface1",
        "TestInterface2",
    }


def test_merge_unions_returns_union_with_merged_types():
    type1 = GraphQLObjectType(name="Type1", fields={"val": GraphQLField(GraphQLFloat)})
    duplicated_type1 = GraphQLObjectType(
        name="Type1", fields={"val": GraphQLField(GraphQLFloat)}
    )
    merged_type1 = GraphQLObjectType(
        name="Type1", fields={"val": GraphQLField(GraphQLFloat)}
    )
    type2 = GraphQLObjectType(name="Type2", fields={"field": GraphQLField(GraphQLInt)})
    merged_type2 = GraphQLObjectType(
        name="Type2", fields={"field": GraphQLField(GraphQLInt)}
    )
    type3 = GraphQLObjectType(
        name="Type3", fields={"field": GraphQLField(GraphQLString)}
    )
    merged_type3 = GraphQLObjectType(
        name="Type3", fields={"field": GraphQLField(GraphQLString)}
    )
    union1 = GraphQLUnionType(name="TestUnion", types=(type1, type2))
    union2 = GraphQLUnionType(name="TestUnion", types=(duplicated_type1, type3))

    merged_union = merge_unions(
        merged_types={
            "Type1": merged_type1,
            "Type2": merged_type2,
            "Type3": merged_type3,
        },
        union1=union1,
        union2=union2,
    )

    assert isinstance(merged_union, GraphQLUnionType)
    assert merged_union is not union1
    assert merged_union is not union2
    assert len(merged_union.types) == 3
    assert merged_type1 in merged_union.types
    assert merged_type2 in merged_union.types
    assert merged_type3 in merged_union.types
