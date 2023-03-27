import pytest
from graphql import GraphQLSchema, build_ast_schema, parse

from ariadne_graphql_proxy import merge_schemas


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
