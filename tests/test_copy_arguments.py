from graphql import (
    GraphQLArgument,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLString,
)

from ariadne_graphql_proxy import copy_arguments


def test_copy_arguments_returns_dict_with_copies_of_arguments():
    related_argument_type = GraphQLInputObjectType(
        name="TypeA", fields={"val": GraphQLInputField(type_=GraphQLString)}
    )
    duplicated_related_argument_type = GraphQLInputObjectType(
        name="TypeA", fields={"val": GraphQLInputField(type_=GraphQLString)}
    )
    arguments = {
        "arg1": GraphQLArgument(
            type_=GraphQLString,
            default_value="default",
            description="arg1 description",
            deprecation_reason="reason",
            out_name="out name",
        ),
        "arg2": GraphQLArgument(type_=related_argument_type),
    }

    copied_arguments = copy_arguments(
        {"TypeA": duplicated_related_argument_type}, arguments
    )

    assert isinstance(copied_arguments["arg1"], GraphQLArgument)
    assert copied_arguments["arg1"] is not arguments["arg1"]
    assert copied_arguments["arg1"].type == GraphQLString
    assert copied_arguments["arg1"].default_value == arguments["arg1"].default_value
    assert copied_arguments["arg1"].description == arguments["arg1"].description
    assert (
        copied_arguments["arg1"].deprecation_reason
        == arguments["arg1"].deprecation_reason
    )
    assert copied_arguments["arg1"].out_name == arguments["arg1"].out_name
    assert isinstance(copied_arguments["arg2"], GraphQLArgument)
    assert copied_arguments["arg2"] is not arguments["arg2"]
    assert copied_arguments["arg2"].type == duplicated_related_argument_type


def test_copy_arguments_returns_dict_without_excluded_arg():
    arguments = {
        "arg1": GraphQLArgument(type_=GraphQLString),
        "arg2": GraphQLArgument(type_=GraphQLString),
    }

    copied_arguments = copy_arguments({}, arguments, field_exclude_args=["arg1"])

    assert "arg1" not in copied_arguments
