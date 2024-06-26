import pytest
from graphql import GraphQLSchema, build_ast_schema, parse

from ariadne_graphql_proxy import copy_schema


def assert_directive_exists(schema: GraphQLSchema, directive_name: str):
    assert directive_name in [d.name for d in schema.directives]


def assert_directive_doesnt_exist(schema: GraphQLSchema, directive_name: str):
    assert directive_name not in [d.name for d in schema.directives]


def test_copy_schema_subset_excludes_unspecified_root_types(gql):
    schema_str = gql(
        """
        type Query {
            lorem: Int!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }

        type Mutation {
            echo(val: String!): String!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Mutation" not in copied_schema.type_map


def test_copy_schema_subset_excludes_unspecified_root_fields(gql):
    schema_str = gql(
        """
        type Query {
            lorem: Int!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert list(copied_schema.query_type.fields) == ["lorem", "dolor"]


def test_copy_schema_subset_raises_exception_for_undefined_root(gql):
    schema_str = gql(
        """
        type Query {
            lorem: Int!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    with pytest.raises(ValueError) as exc_info:
        copy_schema(schema, queries=["lorem", "dolor"], mutations=["echo"])

    assert str(exc_info.value) == ("Root type 'Mutation' is not defined by the schema.")


def test_copy_schema_subset_includes_root_directive(gql):
    schema_str = gql(
        """
        directive @custom on OBJECT

        type Query @custom {
            lorem: Int!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert_directive_exists(copied_schema, "custom")


def test_copy_schema_subset_raises_exception_for_undefined_root_field(gql):
    schema_str = gql(
        """
        type Query {
            lorem: Int!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    with pytest.raises(ValueError) as exc_info:
        copy_schema(schema, queries=["lorem", "echo"])

    assert str(exc_info.value) == (
        "Root type 'Query' is not defining the 'echo' field."
    )


def test_copy_schema_subset_raises_exception_for_specified_excluded_root_field(gql):
    schema_str = gql(
        """
        type Query {
            lorem: Int!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    with pytest.raises(ValueError) as exc_info:
        copy_schema(
            schema,
            queries=["lorem", "dolor"],
            exclude_fields={"Query": ["dolor"]},
        )

    assert str(exc_info.value) == (
        "Field 'dolor' of type 'Query' is specified in both "
        "'exclude_fields' and 'queries'."
    )


def test_copy_schema_subset_raises_exception_for_specified_type_excluded_root_field(
    gql,
):
    schema_str = gql(
        """
        type Query {
            lorem: Int!
            ipsum: Int!
            dolor: Excluded!
            met: Int!
        }

        type Excluded {
            id: ID!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    with pytest.raises(ValueError) as exc_info:
        copy_schema(
            schema,
            queries=["lorem", "dolor"],
            exclude_types=["Excluded"],
        )

    assert str(exc_info.value) == (
        "Field 'dolor' of type 'Query' that is specified in 'queries' has "
        "a return type 'Excluded' that is also specified in 'exclude_types'."
    )


def test_copy_schema_subset_includes_root_field_directive(gql):
    schema_str = gql(
        """
        directive @custom on FIELD_DEFINITION

        type Query {
            lorem: Int!
            ipsum: Int!
            dolor: Int! @custom
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert_directive_exists(copied_schema, "custom")


def test_copy_schema_subset_excludes_unused_root_field_directive(gql):
    schema_str = gql(
        """
        directive @custom on FIELD_DEFINITION

        type Query {
            lorem: Int!
            ipsum: Int!
            dolor: Int!
            met: Int! @custom
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert_directive_doesnt_exist(copied_schema, "custom")


def test_copy_schema_subset_includes_used_root_field_enum_type(gql):
    schema_str = gql(
        """
        enum Role {
            USER
            ADMIN
        }

        type Query {
            lorem: Role!
            ipsum: Int!
            dolor: Int!
            met: Role!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Role" in copied_schema.type_map


def test_copy_schema_subset_excludes_unused_root_field_enum_type(gql):
    schema_str = gql(
        """
        enum Role {
            USER
            ADMIN
        }

        type Query {
            lorem: Int!
            ipsum: Int!
            dolor: Int!
            met: Role!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Role" not in copied_schema.type_map


def test_copy_schema_subset_includes_used_root_field_interface_type(gql):
    schema_str = gql(
        """
        interface Result {
            id: ID!
        }

        type Query {
            lorem: Result!
            ipsum: Int!
            dolor: Int!
            met: Result!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" in copied_schema.type_map


def test_copy_schema_subset_excludes_unused_root_field_interface_type(gql):
    schema_str = gql(
        """
        interface Result {
            id: ID!
        }

        type Query {
            lorem: Int!
            ipsum: Int!
            dolor: Int!
            met: Result!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" not in copied_schema.type_map


def test_copy_schema_subset_includes_used_root_field_object_type(gql):
    schema_str = gql(
        """
        type Result {
            id: ID!
        }

        type Query {
            lorem: Result!
            ipsum: Int!
            dolor: Int!
            met: Result!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" in copied_schema.type_map


def test_copy_schema_subset_excludes_unused_root_field_object_type(gql):
    schema_str = gql(
        """
        type Result {
            id: ID!
        }

        type Query {
            lorem: Int!
            ipsum: Int!
            dolor: Int!
            met: Result!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" not in copied_schema.type_map


def test_copy_schema_subset_includes_used_root_field_scalar_type(gql):
    schema_str = gql(
        """
        scalar Money

        type Query {
            lorem: Money!
            ipsum: Int!
            dolor: Int!
            met: Money!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Money" in copied_schema.type_map


def test_copy_schema_subset_excludes_unused_root_field_scalar_type(gql):
    schema_str = gql(
        """
        scalar Money

        type Query {
            lorem: Int!
            ipsum: Int!
            dolor: Int!
            met: Money!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Money" not in copied_schema.type_map


def test_copy_schema_subset_includes_used_root_field_union_type(gql):
    schema_str = gql(
        """
        type Message {
            message: String!
        }

        type User {
            username: String!
        }

        union Result = Message | User

        type Query {
            lorem: Result!
            ipsum: Int!
            dolor: Int!
            met: Result!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" in copied_schema.type_map


def test_copy_schema_subset_excludes_unused_root_field_union_type(gql):
    schema_str = gql(
        """
        type Message {
            message: String!
        }

        type User {
            username: String!
        }

        union Result = Message | User

        type Query {
            lorem: Int!
            ipsum: Int!
            dolor: Int!
            met: Result!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" not in copied_schema.type_map


def test_copy_schema_subset_excludes_specified_root_field_arg(gql):
    schema_str = gql(
        """
        type Query {
            lorem(arg: Int!): Int!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema,
        queries=["lorem", "dolor"],
        exclude_args={"Query": {"lorem": ["arg"]}},
    )
    assert not copied_schema.type_map["Query"].fields["lorem"].args


def test_copy_schema_subset_includes_root_field_arg_directive(gql):
    schema_str = gql(
        """
        directive @custom on ARGUMENT_DEFINITION

        type Query {
            lorem(arg: Int! @custom): Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert_directive_exists(copied_schema, "custom")


def test_copy_schema_subset_excludes_specified_root_field_arg_directive(gql):
    schema_str = gql(
        """
        directive @custom on ARGUMENT_DEFINITION

        type Query {
            lorem(arg: Int! @custom): Int!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema,
        queries=["lorem", "dolor"],
        exclude_args={"Query": {"lorem": ["arg"]}},
    )
    assert_directive_doesnt_exist(copied_schema, "custom")


def test_copy_schema_subset_excludes_unused_root_field_arg_directive(gql):
    schema_str = gql(
        """
        directive @custom on ARGUMENT_DEFINITION

        type Query {
            lorem: Int!
            ipsum(arg: Int! @custom): Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert_directive_doesnt_exist(copied_schema, "custom")


def test_copy_schema_subset_includes_root_field_arg_enum(gql):
    schema_str = gql(
        """
        enum Role {
            USER
            ADMIN
        }

        type Query {
            lorem(arg: Role!): Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Role" in copied_schema.type_map


def test_copy_schema_subset_excludes_specified_root_field_arg_enum(gql):
    schema_str = gql(
        """
        enum Role {
            USER
            ADMIN
        }

        type Query {
            lorem(arg: Role!): Int!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema,
        queries=["lorem", "dolor"],
        exclude_args={"Query": {"lorem": ["arg"]}},
    )
    assert "Role" not in copied_schema.type_map


def test_copy_schema_subset_excludes_unused_root_field_arg_enum(gql):
    schema_str = gql(
        """
        enum Role {
            USER
            ADMIN
        }

        type Query {
            lorem: Int!
            ipsum(arg: Role!): Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Role" not in copied_schema.type_map


def test_copy_schema_subset_includes_root_field_arg_input(gql):
    schema_str = gql(
        """
        input Search {
            query: String
        }

        type Query {
            lorem(arg: Search!): Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Search" in copied_schema.type_map


def test_copy_schema_subset_excludes_specified_root_field_arg_input(gql):
    schema_str = gql(
        """
        input Search {
            query: String
        }

        type Query {
            lorem(arg: Search!): Int!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema,
        queries=["lorem", "dolor"],
        exclude_args={"Query": {"lorem": ["arg"]}},
    )
    assert "Search" not in copied_schema.type_map


def test_copy_schema_subset_excludes_unused_root_field_arg_input(gql):
    schema_str = gql(
        """
        input Search {
            query: String
        }

        type Query {
            lorem: Int!
            ipsum(arg: Search!): Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Search" not in copied_schema.type_map


def test_copy_schema_subset_includes_root_field_arg_scalar(gql):
    schema_str = gql(
        """
        scalar Money

        type Query {
            lorem(arg: Money!): Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Money" in copied_schema.type_map


def test_copy_schema_subset_excludes_specified_root_field_arg_scalar(gql):
    schema_str = gql(
        """
        scalar Money

        type Query {
            lorem(arg: Money!): Int!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema,
        queries=["lorem", "dolor"],
        exclude_args={"Query": {"lorem": ["arg"]}},
    )
    assert "Money" not in copied_schema.type_map


def test_copy_schema_subset_excludes_unused_root_field_arg_scalar(gql):
    schema_str = gql(
        """
        scalar Money

        type Query {
            lorem: Int!
            ipsum(arg: Money!): Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Money" not in copied_schema.type_map


def test_copy_schema_subset_excludes_directive(gql):
    schema_str = gql(
        """
        directive @custom on FIELD_DEFINITION

        type Query {
            lorem: Int! @custom
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema,
        queries=["lorem", "dolor"],
        exclude_directives=["custom"],
    )
    assert_directive_doesnt_exist(copied_schema, "custom")


def test_copy_schema_subset_includes_directive_arg_type(gql):
    schema_str = gql(
        """
        scalar Score
    
        directive @custom(arg: Score) on FIELD_DEFINITION

        type Query {
            lorem: Int! @custom
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert_directive_exists(copied_schema, "custom")
    assert "Score" in copied_schema.type_map


def test_copy_schema_subset_excludes_directive_arg_and_type(gql):
    schema_str = gql(
        """
        scalar Score
    
        directive @custom(arg: Score) on FIELD_DEFINITION

        type Query {
            lorem: Int! @custom
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema, queries=["lorem", "dolor"], exclude_directives_args={"custom": ["arg"]}
    )
    assert_directive_exists(copied_schema, "custom")
    assert "Score" not in copied_schema.type_map

    directives = {d.name: d for d in copied_schema.directives}
    assert not directives["custom"].args


def test_copy_schema_subset_includes_enum_directive(gql):
    schema_str = gql(
        """
        directive @custom on ENUM

        enum Role @custom {
            USER
            ADMIN
        }

        type Query {
            lorem: Role!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Role" in copied_schema.type_map
    assert_directive_exists(copied_schema, "custom")


def test_copy_schema_subset_includes_enum_value_directive(gql):
    schema_str = gql(
        """
        directive @custom on ENUM_VALUE

        enum Role {
            USER
            ADMIN @custom
        }

        type Query {
            lorem: Role!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Role" in copied_schema.type_map
    assert_directive_exists(copied_schema, "custom")


def test_copy_schema_subset_includes_input_directive(gql):
    schema_str = gql(
        """
        directive @custom on INPUT_OBJECT

        input Search @custom {
            query: String!
        }

        type Query {
            lorem(arg: Search): Int!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Search" in copied_schema.type_map
    assert_directive_exists(copied_schema, "custom")


def test_copy_schema_subset_excludes_input_field(gql):
    schema_str = gql(
        """
        input Search {
            query: String!
            score: Int!
        }

        type Query {
            lorem(arg: Search): Int!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema,
        queries=["lorem", "dolor"],
        exclude_fields={"Search": ["score"]},
    )
    assert "Search" in copied_schema.type_map
    assert "score" not in copied_schema.type_map["Search"].fields


def test_copy_schema_subset_includes_input_field_directive(gql):
    schema_str = gql(
        """
        directive @custom on INPUT_FIELD_DEFINITION

        input Search {
            query: String!
            score: Int! @custom
        }

        type Query {
            lorem(arg: Search): Int!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Search" in copied_schema.type_map
    assert_directive_exists(copied_schema, "custom")


def test_copy_schema_subset_excludes_input_field_directive(gql):
    schema_str = gql(
        """
        directive @custom on INPUT_FIELD_DEFINITION

        input Search {
            query: String!
            score: Int! @custom
        }

        type Query {
            lorem(arg: Search): Int!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema,
        queries=["lorem", "dolor"],
        exclude_fields={"Search": ["score"]},
    )
    assert "Search" in copied_schema.type_map
    assert "score" not in copied_schema.type_map["Search"].fields
    assert_directive_doesnt_exist(copied_schema, "custom")


def test_copy_schema_subset_includes_input_field_type(gql):
    schema_str = gql(
        """
        scalar Score

        input Search {
            query: String!
            score: Score!
        }

        type Query {
            lorem(arg: Search): Int!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Search" in copied_schema.type_map
    assert "Score" in copied_schema.type_map


def test_copy_schema_subset_excludes_input_field_type(gql):
    schema_str = gql(
        """
        scalar Score

        input Search {
            query: String!
            score: Score!
        }

        type Query {
            lorem(arg: Search): Int!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema,
        queries=["lorem", "dolor"],
        exclude_fields={"Search": ["score"]},
    )
    assert "Search" in copied_schema.type_map
    assert "Score" not in copied_schema.type_map


def test_copy_schema_subset_includes_interface_directive(gql):
    schema_str = gql(
        """
        directive @custom on INTERFACE

        interface Result @custom {
            id: ID!
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" in copied_schema.type_map
    assert_directive_exists(copied_schema, "custom")


def test_copy_schema_subset_excludes_interface_directive(gql):
    schema_str = gql(
        """
        directive @custom on INTERFACE

        interface Result @custom {
            id: ID!
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema, queries=["lorem", "dolor"], exclude_directives=["custom"]
    )
    assert "Result" in copied_schema.type_map
    assert_directive_doesnt_exist(copied_schema, "custom")


def test_copy_schema_subset_includes_interface_interface(gql):
    schema_str = gql(
        """
        interface Message {
            message: String!
        }

        interface Result implements Message {
            id: ID!
            message: String!
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" in copied_schema.type_map
    assert "Message" in copied_schema.type_map


def test_copy_schema_subset_exclude_interface_field(gql):
    schema_str = gql(
        """
        interface Result {
            id: ID!
            message: String!
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema,
        queries=["lorem", "dolor"],
        exclude_fields={"Result": ["message"]},
    )
    assert "Result" in copied_schema.type_map
    assert "message" not in copied_schema.type_map["Result"].fields


def test_copy_schema_subset_includes_interface_field_directive(gql):
    schema_str = gql(
        """
        directive @custom on FIELD_DEFINITION

        interface Result {
            id: ID! @custom
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" in copied_schema.type_map
    assert_directive_exists(copied_schema, "custom")


def test_copy_schema_subset_excludes_interface_field_directive(gql):
    schema_str = gql(
        """
        directive @custom on FIELD_DEFINITION

        interface Result {
            id: ID!
            message: String! @custom
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema, queries=["lorem", "dolor"], exclude_fields={"Result": ["message"]}
    )
    assert "Result" in copied_schema.type_map
    assert_directive_doesnt_exist(copied_schema, "custom")


def test_copy_schema_subset_includes_interface_field_type(gql):
    schema_str = gql(
        """
        scalar Money

        interface Result {
            id: ID!
            money: Money
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" in copied_schema.type_map
    assert "Money" in copied_schema.type_map


def test_copy_schema_subset_excludes_interface_field_type(gql):
    schema_str = gql(
        """
        scalar Money

        interface Result {
            id: ID!
            money: Money
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema,
        queries=["lorem", "dolor"],
        exclude_fields={"Result": ["money"]},
    )
    assert "Result" in copied_schema.type_map
    assert "Money" not in copied_schema.type_map


def test_copy_schema_subset_includes_interface_field_arg_directive(gql):
    schema_str = gql(
        """
        directive @custom on ARGUMENT_DEFINITION

        interface Result {
            id: ID!
            message(arg: String! @custom): String!
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" in copied_schema.type_map
    assert "arg" in copied_schema.type_map["Result"].fields["message"].args
    assert_directive_exists(copied_schema, "custom")


def test_copy_schema_subset_excludes_interface_field_arg_directive(gql):
    schema_str = gql(
        """
        directive @custom on ARGUMENT_DEFINITION

        interface Result {
            id: ID!
            message(arg: String! @custom): String!
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema,
        queries=["lorem", "dolor"],
        exclude_args={"Result": {"message": ["arg"]}},
    )
    assert "Result" in copied_schema.type_map
    assert not copied_schema.type_map["Result"].fields["message"].args
    assert_directive_doesnt_exist(copied_schema, "custom")


def test_copy_schema_subset_includes_interface_field_arg_type(gql):
    schema_str = gql(
        """
        scalar Money

        interface Result {
            id: ID!
            tax(arg: Money!): Int!
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" in copied_schema.type_map
    assert "Money" in copied_schema.type_map
    assert "arg" in copied_schema.type_map["Result"].fields["tax"].args


def test_copy_schema_subset_excludes_interface_field_arg_type(gql):
    schema_str = gql(
        """
        scalar Money

        interface Result {
            id: ID!
            tax(arg: Money!): Int!
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema, queries=["lorem", "dolor"], exclude_args={"Result": {"tax": ["arg"]}}
    )
    assert "Result" in copied_schema.type_map
    assert "Money" not in copied_schema.type_map
    assert not copied_schema.type_map["Result"].fields["tax"].args


def test_copy_schema_subset_includes_object_directive(gql):
    schema_str = gql(
        """
        directive @custom on OBJECT

        type Result @custom {
            id: ID!
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" in copied_schema.type_map
    assert_directive_exists(copied_schema, "custom")


def test_copy_schema_subset_excludes_object_directive(gql):
    schema_str = gql(
        """
        directive @custom on OBJECT

        type Result @custom {
            id: ID!
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema, queries=["lorem", "dolor"], exclude_directives=["custom"]
    )
    assert "Result" in copied_schema.type_map
    assert_directive_doesnt_exist(copied_schema, "custom")


def test_copy_schema_subset_includes_object_interface(gql):
    schema_str = gql(
        """
        interface Message {
            message: String!
        }

        type Result implements Message {
            id: ID!
            message: String!
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" in copied_schema.type_map
    assert "Message" in copied_schema.type_map


def test_copy_schema_subset_exclude_object_field(gql):
    schema_str = gql(
        """
        type Result {
            id: ID!
            message: String!
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema,
        queries=["lorem", "dolor"],
        exclude_fields={"Result": ["message"]},
    )
    assert "Result" in copied_schema.type_map
    assert "message" not in copied_schema.type_map["Result"].fields


def test_copy_schema_subset_includes_object_field_directive(gql):
    schema_str = gql(
        """
        directive @custom on FIELD_DEFINITION

        type Result {
            id: ID! @custom
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" in copied_schema.type_map
    assert_directive_exists(copied_schema, "custom")


def test_copy_schema_subset_excludes_object_field_directive(gql):
    schema_str = gql(
        """
        directive @custom on FIELD_DEFINITION

        type Result {
            id: ID!
            message: String! @custom
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema, queries=["lorem", "dolor"], exclude_fields={"Result": ["message"]}
    )
    assert "Result" in copied_schema.type_map
    assert_directive_doesnt_exist(copied_schema, "custom")


def test_copy_schema_subset_includes_object_field_type(gql):
    schema_str = gql(
        """
        scalar Money

        type Result {
            id: ID!
            money: Money
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" in copied_schema.type_map
    assert "Money" in copied_schema.type_map


def test_copy_schema_subset_excludes_object_field_type(gql):
    schema_str = gql(
        """
        scalar Money

        type Result {
            id: ID!
            money: Money
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema,
        queries=["lorem", "dolor"],
        exclude_fields={"Result": ["money"]},
    )
    assert "Result" in copied_schema.type_map
    assert "Money" not in copied_schema.type_map


def test_copy_schema_subset_includes_object_field_arg_directive(gql):
    schema_str = gql(
        """
        directive @custom on ARGUMENT_DEFINITION

        type Result {
            id: ID!
            message(arg: String! @custom): String!
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" in copied_schema.type_map
    assert "arg" in copied_schema.type_map["Result"].fields["message"].args
    assert_directive_exists(copied_schema, "custom")


def test_copy_schema_subset_excludes_object_field_arg_directive(gql):
    schema_str = gql(
        """
        directive @custom on ARGUMENT_DEFINITION

        type Result {
            id: ID!
            message(arg: String! @custom): String!
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema,
        queries=["lorem", "dolor"],
        exclude_args={"Result": {"message": ["arg"]}},
    )
    assert "Result" in copied_schema.type_map
    assert not copied_schema.type_map["Result"].fields["message"].args
    assert_directive_doesnt_exist(copied_schema, "custom")


def test_copy_schema_subset_includes_object_field_arg_type(gql):
    schema_str = gql(
        """
        scalar Money

        type Result {
            id: ID!
            tax(arg: Money!): Int!
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" in copied_schema.type_map
    assert "Money" in copied_schema.type_map
    assert "arg" in copied_schema.type_map["Result"].fields["tax"].args


def test_copy_schema_subset_excludes_object_field_arg_type(gql):
    schema_str = gql(
        """
        scalar Money

        type Result {
            id: ID!
            tax(arg: Money!): Int!
        }

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema, queries=["lorem", "dolor"], exclude_args={"Result": {"tax": ["arg"]}}
    )
    assert "Result" in copied_schema.type_map
    assert "Money" not in copied_schema.type_map
    assert not copied_schema.type_map["Result"].fields["tax"].args


def test_copy_schema_subset_includes_scalar_directive(gql):
    schema_str = gql(
        """
        directive @custom on SCALAR

        scalar Money @custom

        type Query {
            lorem: [Money!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Money" in copied_schema.type_map
    assert_directive_exists(copied_schema, "custom")


def test_copy_schema_subset_excludes_scalar_directive(gql):
    schema_str = gql(
        """
        directive @custom on SCALAR

        scalar Money @custom

        type Query {
            lorem: [Money!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema, queries=["lorem", "dolor"], exclude_directives=["custom"]
    )
    assert "Money" in copied_schema.type_map
    assert_directive_doesnt_exist(copied_schema, "custom")


def test_copy_schema_subset_includes_union_directive(gql):
    schema_str = gql(
        """
        directive @custom on UNION

        type User {
            id: ID!
        }

        type Message {
            message: String!
        }

        union Result @custom = User | Message

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" in copied_schema.type_map
    assert_directive_exists(copied_schema, "custom")


def test_copy_schema_subset_excludes_union_directive(gql):
    schema_str = gql(
        """
        directive @custom on UNION

        type User {
            id: ID!
        }

        type Message {
            message: String!
        }

        union Result @custom = User | Message

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema, queries=["lorem", "dolor"], exclude_directives=["custom"]
    )
    assert "Result" in copied_schema.type_map
    assert_directive_doesnt_exist(copied_schema, "custom")


def test_copy_schema_subset_includes_union_types(gql):
    schema_str = gql(
        """
        type User {
            id: ID!
        }

        type Message {
            message: String!
        }

        union Result = User | Message

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(schema, queries=["lorem", "dolor"])
    assert "Result" in copied_schema.type_map
    assert "User" in copied_schema.type_map
    assert "Message" in copied_schema.type_map

    result_types = [t.name for t in copied_schema.type_map["Result"].types]
    assert result_types == ["User", "Message"]


def test_copy_schema_subset_excludes_union_types(gql):
    schema_str = gql(
        """
        type User {
            id: ID!
        }

        type Message {
            message: String!
        }

        union Result = User | Message

        type Query {
            lorem: [Result!]!
            ipsum: Int!
            dolor: Int!
            met: Int!
        }
        """
    )
    schema = build_ast_schema(parse(schema_str))

    copied_schema = copy_schema(
        schema, queries=["lorem", "dolor"], exclude_types=["Message"]
    )
    assert "Result" in copied_schema.type_map
    assert "User" in copied_schema.type_map
    assert "Message" not in copied_schema.type_map

    assert len(copied_schema.type_map["Result"].types) == 1
    assert copied_schema.type_map["Result"].types[0].name == "User"
