import pytest

from ariadne_graphql_proxy import unset_resolver


def mock_resolver(*args):
    pass


def test_unset_resolver_removes_resolver_from_specified_field(schema):
    schema.type_map["Query"].fields["complex"].resolve = mock_resolver
    assert schema.type_map["Query"].fields["complex"].resolve is mock_resolver

    unset_resolver(schema, "Query", "complex")
    assert schema.type_map["Query"].fields["complex"].resolve is None


def test_unset_resolver_does_nothing_if_field_already_has_no_resolver(schema):
    assert schema.type_map["Query"].fields["complex"].resolve is None

    unset_resolver(schema, "Query", "complex")
    assert schema.type_map["Query"].fields["complex"].resolve is None


def test_unset_resolver_raises_error_if_type_doesnt_exist(schema):
    with pytest.raises(ValueError) as exc_info:
        unset_resolver(schema, "Other", "complex")

    assert "'Other' doesn't exist" in str(exc_info.value)


def test_unset_resolver_raises_error_if_type_is_not_object(search_schema):
    with pytest.raises(ValueError) as exc_info:
        unset_resolver(search_schema, "Result", "complex")

    assert "Expected 'Result' to be a 'type'" in str(exc_info.value)


def test_unset_resolver_raises_error_if_type_has_no_field(search_schema):
    with pytest.raises(ValueError) as exc_info:
        unset_resolver(search_schema, "Query", "complex")

    assert "Type 'Query' doesn't have a field named 'complex'" in str(exc_info.value)
