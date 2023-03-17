import pytest
from graphql import (
    GraphQLArgument,
    GraphQLFloat,
    GraphQLInt,
    GraphQLList,
    GraphQLNonNull,
    GraphQLString,
)

from ariadne_graphql_proxy.merge import (
    merge_args,
)


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


def test_merge_args_returns_arg_with_default_value_from_first_arg():
    arg1 = GraphQLArgument(
        type_=GraphQLString,
        default_value="default",
    )
    arg2 = GraphQLArgument(
        type_=GraphQLString,
    )

    merged_args = merge_args({}, {"arg1": arg1}, {"arg1": arg2})

    assert isinstance(merged_args["arg1"], GraphQLArgument)
    assert merged_args["arg1"].default_value == "default"


def test_merge_args_returns_arg_with_default_value_from_other_arg():
    arg1 = GraphQLArgument(
        type_=GraphQLString,
    )
    arg2 = GraphQLArgument(
        type_=GraphQLString,
        default_value="default",
    )

    merged_args = merge_args({}, {"arg1": arg1}, {"arg1": arg2})

    assert isinstance(merged_args["arg1"], GraphQLArgument)
    assert merged_args["arg1"].default_value == "default"


def test_merge_args_raises_type_error_for_not_matching_default_values():
    arg1 = GraphQLArgument(
        type_=GraphQLString,
        default_value="default",
    )
    arg2 = GraphQLArgument(
        type_=GraphQLString,
        default_value="other",
    )

    with pytest.raises(TypeError):
        merge_args({}, {"arg1": arg1}, {"arg1": arg2})


def test_merge_args_returns_arg_with_description_from_first_arg():
    arg1 = GraphQLArgument(
        type_=GraphQLString,
        description="Hello world!",
    )
    arg2 = GraphQLArgument(
        type_=GraphQLString,
    )

    merged_args = merge_args({}, {"arg1": arg1}, {"arg1": arg2})

    assert isinstance(merged_args["arg1"], GraphQLArgument)
    assert merged_args["arg1"].description == "Hello world!"


def test_merge_args_returns_arg_with_description_from_other_arg():
    arg1 = GraphQLArgument(
        type_=GraphQLString,
    )
    arg2 = GraphQLArgument(
        type_=GraphQLString,
        description="Hello world!",
    )

    merged_args = merge_args({}, {"arg1": arg1}, {"arg1": arg2})

    assert isinstance(merged_args["arg1"], GraphQLArgument)
    assert merged_args["arg1"].description == "Hello world!"


def test_merge_args_raises_type_error_for_not_matching_descriptions():
    arg1 = GraphQLArgument(
        type_=GraphQLString,
        description="Lorem ipsum",
    )
    arg2 = GraphQLArgument(
        type_=GraphQLString,
        description="Dolor met",
    )

    with pytest.raises(TypeError):
        merge_args({}, {"arg1": arg1}, {"arg1": arg2})


def test_merge_args_returns_arg_with_deprecation_reason_from_first_arg():
    arg1 = GraphQLArgument(
        type_=GraphQLString,
        deprecation_reason="Hello world!",
    )
    arg2 = GraphQLArgument(
        type_=GraphQLString,
    )

    merged_args = merge_args({}, {"arg1": arg1}, {"arg1": arg2})

    assert isinstance(merged_args["arg1"], GraphQLArgument)
    assert merged_args["arg1"].deprecation_reason == "Hello world!"


def test_merge_args_returns_arg_with_deprecation_reason_from_other_arg():
    arg1 = GraphQLArgument(
        type_=GraphQLString,
    )
    arg2 = GraphQLArgument(
        type_=GraphQLString,
        deprecation_reason="Hello world!",
    )

    merged_args = merge_args({}, {"arg1": arg1}, {"arg1": arg2})

    assert isinstance(merged_args["arg1"], GraphQLArgument)
    assert merged_args["arg1"].deprecation_reason == "Hello world!"


def test_merge_args_raises_type_error_for_not_matching_deprecation_reasons():
    arg1 = GraphQLArgument(
        type_=GraphQLString,
        deprecation_reason="Lorem ipsum",
    )
    arg2 = GraphQLArgument(
        type_=GraphQLString,
        deprecation_reason="Dolor met",
    )

    with pytest.raises(TypeError):
        merge_args({}, {"arg1": arg1}, {"arg1": arg2})


def test_merge_args_returns_arg_with_out_name_from_first_arg():
    arg1 = GraphQLArgument(
        type_=GraphQLString,
        out_name="test_field",
    )
    arg2 = GraphQLArgument(
        type_=GraphQLString,
    )

    merged_args = merge_args({}, {"arg1": arg1}, {"arg1": arg2})

    assert isinstance(merged_args["arg1"], GraphQLArgument)
    assert merged_args["arg1"].out_name == "test_field"


def test_merge_args_returns_arg_with_out_name_from_other_arg():
    arg1 = GraphQLArgument(
        type_=GraphQLString,
    )
    arg2 = GraphQLArgument(
        type_=GraphQLString,
        out_name="test_field",
    )

    merged_args = merge_args({}, {"arg1": arg1}, {"arg1": arg2})

    assert isinstance(merged_args["arg1"], GraphQLArgument)
    assert merged_args["arg1"].out_name == "test_field"


def test_merge_args_raises_type_error_for_not_matching_out_names():
    arg1 = GraphQLArgument(
        type_=GraphQLString,
        out_name="test_field",
    )
    arg2 = GraphQLArgument(
        type_=GraphQLString,
        out_name="test_field_other",
    )

    with pytest.raises(TypeError):
        merge_args({}, {"arg1": arg1}, {"arg1": arg2})
