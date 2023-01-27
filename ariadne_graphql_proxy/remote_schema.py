from typing import Optional

import httpx
from ariadne import gql
from graphql import (
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLEnumType,
    GraphQLField,
    GraphQLFieldResolver,
    GraphQLFloat,
    GraphQLID,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLInt,
    GraphQLInterfaceType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLString,
    GraphQLUnionType,
)

from .resolvers import set_resolver
from .standard_types import STANDARD_TYPES


class GraphQLRemoteSchema(GraphQLSchema):
    schema_url: str
    _introspection_operation: str
    _introspection_query: str

    def __init__(
        self,
        schema_url: str,
        *,
        introspection_operation: Optional[str] = None,
        introspection_query: Optional[str] = None,
    ):
        self.schema_url = schema_url
        self._introspection_operation = (
            introspection_operation or "AriadneGraphQLProxyIntrospection"
        )
        self._introspection_query = introspection_query or INTROSPECTION_QUERY

        introspection_result = self.introspect_remote_schema()
        remote_types = self.get_remote_schema_types(introspection_result["types"])

        query = None
        mutation = None

        if introspection_result["queryType"]:
            query = remote_types[introspection_result["queryType"]["name"]]
        if introspection_result["mutationType"]:
            mutation = remote_types[introspection_result["mutationType"]["name"]]

        super().__init__(query=query, mutation=mutation, types=remote_types.values())

    def introspect_remote_schema(self):
        result = httpx.post(
            self.schema_url,
            json={
                "operationName": self._introspection_operation,
                "query": self._introspection_query,
            },
        )

        if result.status_code != 200:
            raise Exception("Error", result)

        return result.json()["data"]["__schema"]

    def get_remote_schema_types(self, introspection_result):
        types_map = {}
        for introspected_type in introspection_result:
            if introspected_type["name"] in STANDARD_TYPES:
                continue

            types_map[introspected_type["name"]] = self.get_remote_type(
                types_map, introspected_type
            )
        return types_map

    def get_remote_type(self, types_map, type_data):
        if type_data["kind"] == "SCALAR":
            return self.get_remote_scalar(type_data)
        if type_data["kind"] == "ENUM":
            return self.get_remote_enum(type_data)
        if type_data["kind"] == "OBJECT":
            return self.get_remote_object(types_map, type_data)
        if type_data["kind"] == "INTERFACE":
            return self.get_remote_interface(types_map, type_data)
        if type_data["kind"] == "INPUT_OBJECT":
            return self.get_remote_input(types_map, type_data)
        if type_data["kind"] == "UNION":
            return self.get_remote_union(types_map, type_data)

        raise NotImplementedError(f"Unknown GraphQL kind: '{type_data['kind']}'")

    def get_remote_scalar(self, type_data):
        return GraphQLScalarType(name=type_data["name"])

    def get_remote_enum(self, type_data):
        return GraphQLEnumType(
            name=type_data["name"],
            values={value["name"]: value["name"] for value in type_data["enumValues"]},
        )

    def get_remote_object(self, types_map, type_data):
        def thunk():
            return {
                field["name"]: GraphQLField(
                    self.get_remote_object_field(types_map, field["type"]),
                    self.get_remote_object_field_args(types_map, field["args"]),
                )
                for field in type_data["fields"]
            }

        return GraphQLObjectType(
            name=type_data["name"],
            fields=thunk,
        )

    def get_remote_object_field(self, types_map, field):
        if field["kind"] == "NON_NULL":
            return GraphQLNonNull(
                self.get_remote_object_field(types_map, field["ofType"])
            )

        if field["kind"] == "LIST":
            return GraphQLList(self.get_remote_object_field(types_map, field["ofType"]))

        if field["kind"] in ("OBJECT", "INTERFACE", "ENUM", "UNION", "INPUT_OBJECT"):
            return types_map[field["name"]]

        if field["kind"] == "SCALAR":
            if field["name"] == "ID":
                return GraphQLID
            if field["name"] == "Int":
                return GraphQLInt
            if field["name"] == "String":
                return GraphQLString
            if field["name"] == "Float":
                return GraphQLFloat
            if field["name"] == "Boolean":
                return GraphQLBoolean

            if field["name"] in types_map:
                # return GraphQLInt
                return types_map[field["name"]]

        raise NotImplementedError(f"Unknown GraphQL field kind: '{field['kind']}'")

    def get_remote_object_field_args(self, types_map, args_data):
        if not args_data:
            return None
        args = {}
        for arg in args_data:
            args[arg["name"]] = GraphQLArgument(
                self.get_remote_object_field_arg(types_map, arg["type"]),
                default_value=arg["defaultValue"],
            )
        return args

    def get_remote_object_field_arg(self, types_map, arg):
        if arg["kind"] == "NON_NULL":
            return GraphQLNonNull(
                self.get_remote_object_field_arg(types_map, arg["ofType"])
            )

        if arg["kind"] == "LIST":
            return GraphQLList(
                self.get_remote_object_field_arg(types_map, arg["ofType"])
            )

        if arg["kind"] == "INPUT_OBJECT":
            return types_map[arg["name"]]

        if arg["kind"] == "ENUM":
            return types_map[arg["name"]]

        if arg["kind"] == "SCALAR":
            if arg["name"] == "ID":
                return GraphQLID
            if arg["name"] == "Int":
                return GraphQLInt
            if arg["name"] == "String":
                return GraphQLString
            if arg["name"] == "Float":
                return GraphQLFloat
            if arg["name"] == "Boolean":
                return GraphQLBoolean

            return types_map[arg["name"]]

        raise NotImplementedError(f"Unknown GraphQL argument kind: '{arg['kind']}'")

    def get_remote_interface(self, types_map, type_data):
        def thunk():
            return {
                field["name"]: GraphQLField(
                    self.get_remote_object_field(types_map, field["type"])
                )
                for field in type_data["fields"]
            }

        return GraphQLInterfaceType(
            name=type_data["name"],
            fields=thunk,
        )

    def get_remote_input(self, types_map, type_data):
        def thunk():
            return {
                field["name"]: GraphQLInputField(
                    self.get_remote_object_field(types_map, field["type"]),
                    default_value=field["defaultValue"],
                )
                for field in type_data["inputFields"]
            }

        return GraphQLInputObjectType(
            type_data["name"],
            fields=thunk,
        )

    def get_remote_union(self, types_map, type_data):
        possible_types = [t["name"] for t in type_data["possibleTypes"]]

        def create_thunk(types_map, possible_types):
            def thunk():
                return [types_map[type_name] for type_name in possible_types]

            return thunk

        return GraphQLUnionType(
            name=type_data["name"],
            types=create_thunk(types_map, possible_types),
        )

    def set_resolver(
        self,
        type_name: str,
        field_name: str,
        resolver: GraphQLFieldResolver,
    ):
        set_resolver(self, type_name, field_name, resolver)


INTROSPECTION_QUERY = gql(
    """
    query AriadneGraphQLProxyIntrospection {
        __schema {
            queryType {
                name
            }
            mutationType {
                name
            }
            types {
                name
                kind
                fields {
                    name
                    type {
                        name
                        kind
                        ofType {
                            name
                            kind
                            ofType {
                                name
                                kind
                                ofType {
                                    name
                                    kind
                                    ofType {
                                        name
                                        kind
                                    }
                                }
                            }
                        }
                    }
                    args {
                        name
                        type {
                            name
                            kind
                            ofType {
                                name
                                kind
                                ofType {
                                    name
                                    kind
                                    ofType {
                                        name
                                        kind
                                        ofType {
                                            name
                                            kind
                                        }
                                    }
                                }
                            }
                        }
                        defaultValue
                    }
                }
                inputFields {
                    name
                    type {
                        name
                        kind
                        ofType {
                            name
                            kind
                            ofType {
                                name
                                kind
                                ofType {
                                    name
                                    kind
                                    ofType {
                                        name
                                        kind
                                    }
                                }
                            }
                        }
                    }
                    defaultValue
                }
                enumValues {
                    name
                }
                possibleTypes {
                    name
                }
            }
        }
    }
    """
)
