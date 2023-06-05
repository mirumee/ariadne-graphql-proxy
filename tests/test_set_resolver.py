import pytest

from ariadne_graphql_proxy import set_resolver


def mock_resolver(*args):
    pass


def test_set_resolver_sets_resolver_on_specified_field(schema):
    assert schema.type_map["Query"].fields["complex"].resolve is None

    set_resolver(schema, "Query", "complex", mock_resolver)
    assert schema.type_map["Query"].fields["complex"].resolve is mock_resolver


def test_set_resolver_removes_resolver_from_specified_field(schema):
    schema.type_map["Query"].fields["complex"].resolve = mock_resolver
    assert schema.type_map["Query"].fields["complex"].resolve is mock_resolver

    set_resolver(schema, "Query", "complex", None)
    assert schema.type_map["Query"].fields["complex"].resolve is None


def test_set_resolver_raises_error_if_type_doesnt_exist(schema):
    with pytest.raises(ValueError) as exc_info:
        set_resolver(schema, "Other", "complex", mock_resolver)

    assert "'Other' doesn't exist" in str(exc_info.value)


def test_set_resolver_raises_error_if_type_is_not_object(search_schema):
    with pytest.raises(ValueError) as exc_info:
        set_resolver(search_schema, "Result", "complex", mock_resolver)

    assert "Expected 'Result' to be a 'type'" in str(exc_info.value)


def test_set_resolver_raises_error_if_type_has_no_field(search_schema):
    with pytest.raises(ValueError) as exc_info:
        set_resolver(search_schema, "Query", "complex", mock_resolver)

    assert "Type 'Query' doesn't have a field named 'complex'" in str(exc_info.value)
