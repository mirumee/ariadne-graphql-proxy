import pytest
from graphql import GraphQLError, parse

from ariadne_graphql_proxy import get_operation


def test_only_anonymous_operation_is_returned():
    document = parse("{ hello }")
    assert get_operation(document)


def test_only_named_operation_is_returned():
    document = parse("query Hello { hello }")
    operation = get_operation(document)
    assert operation.name.value == "Hello"


def test_only_named_operation_is_returned_by_name():
    document = parse("query Hello { hello }")
    operation = get_operation(document, "Hello")
    assert operation.name.value == "Hello"


def test_named_operation_is_returned_by_name():
    document = parse(
        """
        query Hello { hello }
        
        query User { user { id name } }
        """
    )
    operation = get_operation(document, "User")
    assert operation.name.value == "User"


def test_error_is_raised_if_operation_with_name_is_not_found():
    with pytest.raises(GraphQLError) as excinfo:
        document = parse(
            """
            query Hello { hello }
            
            query User { user { id name } }
            """
        )
        get_operation(document, "Test")

    assert "Unknown operation named 'Test'." == str(excinfo.value)


def test_error_is_raised_if_multiple_operations_are_defined_but_no_name_is_given():
    with pytest.raises(GraphQLError) as excinfo:
        document = parse(
            """
            query Hello { hello }
            
            query User { user { id name } }
            """
        )
        get_operation(document)

    assert "Operation name is required" in str(excinfo.value)


def test_error_is_raised_if_query_has_multiple_anonymous_operations():
    with pytest.raises(GraphQLError) as excinfo:
        document = parse(
            """
            { hello }
            
            { user { id name } }
            """
        )
        get_operation(document)

    assert "Query can't define multiple anonymous operations." == str(excinfo.value)


def test_error_is_raised_if_query_has_combines_anonymous_and_named_operations():
    with pytest.raises(GraphQLError) as excinfo:
        document = parse(
            """
            query Hello { hello }
            
            { user { id name } }
            """
        )
        get_operation(document)

    assert "Query can't define both anonymous and named operations." == str(
        excinfo.value
    )
