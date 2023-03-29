from graphql import (
    GraphQLScalarType,
    ScalarTypeDefinitionNode,
    ScalarTypeExtensionNode,
)

from ariadne_graphql_proxy import copy_scalar


def test_copy_scalar_returns_new_scalar_object():
    scalar_type = GraphQLScalarType(
        name="ScalarName",
        serialize=lambda: None,
        parse_value=lambda: None,
        parse_literal=lambda: None,
        description="description",
        specified_by_url="randomurl.com",
        extensions={"ext1": None},
        ast_node=ScalarTypeDefinitionNode(),
        extension_ast_nodes=[ScalarTypeExtensionNode()],
    )

    copied_type = copy_scalar(scalar_type)

    assert isinstance(copied_type, GraphQLScalarType)
    assert copied_type is not scalar_type
    assert copied_type.name == scalar_type.name
    assert copied_type.serialize == scalar_type.serialize
    assert copied_type.parse_value == scalar_type.parse_value
    assert copied_type.parse_literal == scalar_type.parse_literal
    assert copied_type.description == scalar_type.description
    assert copied_type.specified_by_url == scalar_type.specified_by_url
    assert copied_type.extensions == scalar_type.extensions
    assert copied_type.ast_node == scalar_type.ast_node
    assert copied_type.extension_ast_nodes == scalar_type.extension_ast_nodes
