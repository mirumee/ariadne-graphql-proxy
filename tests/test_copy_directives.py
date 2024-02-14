from unittest.mock import call

from graphql import (
    DirectiveLocation,
    GraphQLArgument,
    GraphQLDirective,
    GraphQLString,
)

from ariadne_graphql_proxy import copy_directives


def test_copy_directives_calls_copy_directive_for_each_object(mocker):
    directive1 = GraphQLDirective(
        name="testDirective", locations=(DirectiveLocation.FIELD,)
    )
    directive2 = GraphQLDirective(
        name="testDirective", locations=(DirectiveLocation.OBJECT,)
    )
    mocked_copy_directive = mocker.patch("ariadne_graphql_proxy.copy.copy_directive")

    copy_directives({}, (directive1, directive2))

    assert mocked_copy_directive.call_count == 2
    mocked_copy_directive.assert_has_calls(
        [
            call({}, directive1, directive_exclude_args=None),
            call({}, directive2, directive_exclude_args=None),
        ]
    )


def test_copy_directives_returns_tuple_without_excluded_directive():
    copied_directives = copy_directives(
        {},
        (
            GraphQLDirective(
                name="testDirectiveA", locations=(DirectiveLocation.FIELD,)
            ),
            GraphQLDirective(
                name="testDirectiveB", locations=(DirectiveLocation.FIELD,)
            ),
        ),
        exclude_directives=["testDirectiveB"],
    )

    assert len(copied_directives) == 1
    assert copied_directives[0].name != "testDirectiveB"


def test_copy_directives_returns_tuple_with_directive_without_excluded_arg():
    copied_directives = copy_directives(
        {},
        (
            GraphQLDirective(
                name="testDirective",
                locations=(DirectiveLocation.FIELD,),
                args={
                    "arg1": GraphQLArgument(type_=GraphQLString),
                    "arg2": GraphQLArgument(type_=GraphQLString),
                },
            ),
        ),
        exclude_directives_args={"testDirective": ["arg1"]},
    )

    assert len(copied_directives) == 1
    assert copied_directives[0].name == "testDirective"
    assert "arg1" not in copied_directives[0].args
