from graphql import (
    DirectiveLocation,
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLDirective,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLString,
)

from ariadne_graphql_proxy import copy_directive


def test_copy_directive_returns_new_directive_object():
    related_arg_type = GraphQLInputObjectType(
        name="InputType", fields={"field1": GraphQLInputField(GraphQLBoolean)}
    )
    duplicated_related_arg_type = GraphQLInputObjectType(
        name="InputType", fields={"field1": GraphQLInputField(GraphQLBoolean)}
    )
    directive = GraphQLDirective(
        name="testDirective",
        locations=(DirectiveLocation.FIELD, DirectiveLocation.OBJECT),
        args={
            "arg1": GraphQLArgument(
                type_=GraphQLString, description="arg1 description"
            ),
            "arg2": GraphQLArgument(type_=related_arg_type),
        },
        is_repeatable=True,
        description="description",
        extensions={"ext": None},
    )

    copied_directive = copy_directive(
        {"InputType": duplicated_related_arg_type}, directive
    )

    assert isinstance(copied_directive, GraphQLDirective)
    assert copied_directive is not directive
    assert copied_directive.name == directive.name
    assert copied_directive.locations == directive.locations
    assert isinstance(copied_directive.args["arg1"], GraphQLArgument)
    assert copied_directive.args["arg1"].type == GraphQLString
    assert copied_directive.args["arg1"].description == "arg1 description"
    assert isinstance(copied_directive.args["arg2"], GraphQLArgument)
    assert copied_directive.args["arg2"].type == duplicated_related_arg_type
    assert copied_directive.is_repeatable == directive.is_repeatable
    assert copied_directive.description == directive.description
    assert copied_directive.extensions == directive.extensions


def test_copy_directive_returns_directive_without_excluded_arg():
    directive = GraphQLDirective(
        name="testDirective",
        locations=(DirectiveLocation.FIELD,),
        args={
            "arg1": GraphQLArgument(type_=GraphQLString),
            "arg2": GraphQLArgument(type_=GraphQLString),
        },
    )

    copied_directive = copy_directive({}, directive, directive_exclude_args=["arg1"])

    assert isinstance(copied_directive, GraphQLDirective)
    assert copied_directive is not directive
    assert "arg1" not in copied_directive.args
