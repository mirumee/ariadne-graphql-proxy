from unittest.mock import Mock

import pytest
from graphql import graphql_sync

from ariadne_graphql_proxy import set_resolver
from ariadne_graphql_proxy.cache import get_info_cache_key


def caching_resolver(obj, info, **kwargs):
    info.context.append(get_info_cache_key(obj, info, kwargs))
    if isinstance(obj, dict):
        return obj.get(info.field_name)
    return getattr(obj, info.field_name)


@pytest.fixture
def schema_with_cache(schema):
    set_resolver(schema, "Query", "basic", caching_resolver)
    set_resolver(schema, "Query", "complex", caching_resolver)
    return schema


def test_cache_key_is_created_for_leaf_field(schema_with_cache, root_value):
    context = []

    result = graphql_sync(
        schema_with_cache,
        "{ basic }",
        root_value=root_value,
        context_value=context,
    )

    assert not result.errors
    assert context


def test_cache_key_is_created_for_field_with_subselection(
    schema_with_cache, root_value
):
    context = []

    result = graphql_sync(
        schema_with_cache,
        "{ complex { id name class } }",
        root_value=root_value,
        context_value=context,
    )

    assert not result.errors
    assert context


def test_cache_key_is_created_for_field_with_deep_subselection(
    schema_with_cache, root_value
):
    context = []

    result = graphql_sync(
        schema_with_cache,
        "{ complex { id name class group { id name rank } } }",
        root_value=root_value,
        context_value=context,
    )

    assert not result.errors
    assert context


def test_fields_order_has_no_affect_on_cache_key(schema_with_cache, root_value):
    context = []

    result = graphql_sync(
        schema_with_cache,
        "{ complex { id name class } }",
        root_value=root_value,
        context_value=context,
    )

    result = graphql_sync(
        schema_with_cache,
        "{ complex { name id class } }",
        root_value=root_value,
        context_value=context,
    )
    assert not result.errors

    result = graphql_sync(
        schema_with_cache,
        "{ complex { class name id  } }",
        root_value=root_value,
        context_value=context,
    )
    assert not result.errors

    assert len(context) == 3
    assert len(set(context)) == 1


def test_fields_aliases_have_no_affect_on_cache_key(schema_with_cache, root_value):
    context = []

    result = graphql_sync(
        schema_with_cache,
        "{ complex { id name class } }",
        root_value=root_value,
        context_value=context,
    )
    assert not result.errors

    result = graphql_sync(
        schema_with_cache,
        "{ alias: complex { id title: name class } }",
        root_value=root_value,
        context_value=context,
    )
    assert not result.errors

    assert len(context) == 2
    assert len(set(context)) == 1


def test_fields_arguments_are_used_in_cache_key(schema_with_cache, root_value):
    context = []

    result = graphql_sync(
        schema_with_cache,
        "{ basic }",
        root_value=root_value,
        context_value=context,
    )
    assert not result.errors

    result = graphql_sync(
        schema_with_cache,
        "{ basic(arg: true) }",
        root_value=root_value,
        context_value=context,
    )
    assert not result.errors

    assert len(context) == 2
    assert len(set(context)) == 2


def test_fields_arguments_order_has_no_effect_on_cache_key(
    schema_with_cache, root_value
):
    context = []

    result = graphql_sync(
        schema_with_cache,
        "{ basic(arg: true, other: false) }",
        root_value=root_value,
        context_value=context,
    )
    assert not result.errors

    result = graphql_sync(
        schema_with_cache,
        "{ basic(other: false, arg: true) }",
        root_value=root_value,
        context_value=context,
    )
    assert not result.errors

    assert len(context) == 2
    assert len(set(context)) == 1


def test_fragments_are_expanded_for_cache_key(schema_with_cache, root_value):
    context = []

    result = graphql_sync(
        schema_with_cache,
        """
        query {
            complex {
                id
                name
            }
        }
        """,
        root_value=root_value,
        context_value=context,
    )
    assert not result.errors

    result = graphql_sync(
        schema_with_cache,
        """
        query {
            complex {
                ... ComplexData
            }
        }

        fragment ComplexData on Complex {
            id
            name
        }
        """,
        root_value=root_value,
        context_value=context,
    )
    assert not result.errors

    assert len(context) == 2
    assert len(set(context)) == 1


def test_variables_are_used_in_cache_key(schema_with_cache, root_value):
    context = []

    query = """
    query Test($arg: Generic, $other: Generic) {
        basic(arg: $arg, other: $other)
    }
    """

    result = graphql_sync(
        schema_with_cache,
        query,
        root_value=root_value,
        context_value=context,
        variable_values={"arg": 1, "other": True},
    )
    assert not result.errors

    result = graphql_sync(
        schema_with_cache,
        query,
        root_value=root_value,
        context_value=context,
        variable_values={"arg": 1, "other": False},
    )
    assert not result.errors

    assert len(context) == 2
    assert len(set(context)) == 2


def test_variables_ordering_has_no_effect_on_cache_key(schema_with_cache, root_value):
    context = []

    query = """
    query Test($arg: Generic, $other: Generic) {
        basic(arg: $arg, other: $other)
    }
    """

    result = graphql_sync(
        schema_with_cache,
        query,
        root_value=root_value,
        context_value=context,
        variable_values={
            "arg": 1,
            "other": True,
        },
    )
    assert not result.errors

    result = graphql_sync(
        schema_with_cache,
        query,
        root_value=root_value,
        context_value=context,
        variable_values={
            "other": True,
            "arg": 1,
        },
    )
    assert not result.errors

    assert len(context) == 2
    assert len(set(context)) == 1


def test_obj_is_included_in_cache_key(schema_with_cache, root_value):
    context = []

    result = graphql_sync(
        schema_with_cache,
        "{ basic }",
        root_value={"basic": "hello"},
        context_value=context,
    )
    assert not result.errors

    result = graphql_sync(
        schema_with_cache,
        "{ basic }",
        root_value=Mock(basic="hello"),
        context_value=context,
    )
    assert not result.errors

    result = graphql_sync(
        schema_with_cache,
        "{ basic }",
        root_value={"basic": "other"},
        context_value=context,
    )
    assert not result.errors

    assert len(context) == 3
    assert len(set(context)) == 3
