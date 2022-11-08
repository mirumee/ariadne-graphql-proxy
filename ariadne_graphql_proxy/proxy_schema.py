import httpx
from ariadne import gql
from graphql import (
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLEnumType,
    GraphQLField,
    GraphQLFloat,
    GraphQLID,
    GraphQLInputObjectType,
    GraphQLInputField,
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


def make_proxy_schema(schema_url: str) -> GraphQLSchema:
    introspection = make_introspection_query(schema_url)
    schema_types = get_proxy_types_for_schema(introspection["types"])

    query = None
    mutation = None

    if introspection["queryType"]:
        query = schema_types[introspection["queryType"]["name"]]
    if introspection["mutationType"]:
        mutation = schema_types[introspection["mutationType"]["name"]]

    return GraphQLSchema(query=query, mutation=mutation)


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

def make_introspection_query(schema_url: str):
    result = httpx.post(
        schema_url,
        json={
            "operationName": "AriadneGraphQLProxyIntrospection",
            "query": INTROSPECTION_QUERY,
        },
    )

    if result.status_code != 200:
        raise Exception("Error", result)

    return result.json()["data"]["__schema"]


STANDARD_TYPES = (
    "Boolean",
    "Float",
    "Int",
    "String",
    "__Schema",
    "__Type",
    "__TypeKind",
    "__Field",
    "__InputValue",
    "__EnumValue",
    "__Directive",
    "__DirectiveLocation",
)


def get_proxy_types_for_schema(introspection_types):
    types_map = {}
    for item in introspection_types:
        if item["name"] in STANDARD_TYPES:
            continue

        types_map[item["name"]] = get_proxy_type_for_schema(types_map, item)
    return types_map


def get_proxy_type_for_schema(types_map, type_data):
    if type_data["kind"] == "SCALAR":
        return get_proxy_scalar_type(type_data)
    if type_data["kind"] == "ENUM":
        return get_proxy_enum_type(type_data)
    if type_data["kind"] == "OBJECT":
        return get_proxy_object_type(types_map, type_data)
    if type_data["kind"] == "INTERFACE":
        return get_proxy_interface_type(types_map, type_data)
    if type_data["kind"] == "INPUT_OBJECT":
        return get_proxy_input_type(types_map, type_data)
    if type_data["kind"] == "UNION":
        return get_proxy_union_type(types_map, type_data)
    
    raise NotImplementedError(f"Uknown GraphQL kind: '{type_data['kind']}'")


def get_proxy_scalar_type(type_data):
    return GraphQLScalarType(name=type_data["name"])


def get_proxy_enum_type(type_data):
    return GraphQLEnumType(
        name=type_data["name"],
        values={
            value["name"]: value["name"]
            for value in type_data["enumValues"]
        },
    )


def get_proxy_object_type(types_map, type_data):
    def thunk():
        return {
            field["name"]: GraphQLField(
                get_proxy_object_field(types_map, field["type"]),
                get_proxy_object_field_args(types_map, field["args"]),
            )
            for field in type_data["fields"]
        }

    return GraphQLObjectType(
        name=type_data["name"],
        fields=thunk,
    )


def get_proxy_object_field(types_map, field_type):
    if field_type["kind"] == "NON_NULL":
        return GraphQLNonNull(
            get_proxy_object_field(types_map, field_type["ofType"])
        )

    if field_type["kind"] == "LIST":
        return GraphQLList(
            get_proxy_object_field(types_map, field_type["ofType"])
        )
    
    if field_type["kind"] in ("OBJECT", "INTERFACE", "ENUM", "UNION", "INPUT_OBJECT"):
        return types_map[field_type["name"]]

    if field_type["kind"] == "SCALAR":
        if field_type["name"] == "ID":
            return GraphQLID
        if field_type["name"] == "Int":
            return GraphQLInt
        if field_type["name"] == "String":
            return GraphQLString
        if field_type["name"] == "Float":
            return GraphQLFloat
        if field_type["name"] == "Boolean":
            return GraphQLBoolean

        if field_type["name"] in types_map:
            # return GraphQLInt
            return types_map[field_type["name"]]

    raise Exception(field_type)


def get_proxy_object_field_args(types_map, args_data):
    if not args_data:
        return None

    args = {}
    for arg in args_data:
        args[arg["name"]] = GraphQLArgument(
            get_proxy_object_field_arg(types_map, arg["type"])
        )
    return args


def get_proxy_object_field_arg(types_map, arg):
    if arg["kind"] == "NON_NULL":
        return GraphQLNonNull(
            get_proxy_object_field_arg(types_map, arg["ofType"])
        )

    if arg["kind"] == "INPUT_OBJECT":
        return types_map[arg["name"]]
    
    raise Exception(arg)


def get_proxy_interface_type(types_map, type_data):
    def thunk():
        return {
            field["name"]: GraphQLField(get_proxy_object_field(types_map, field["type"]))
            for field in type_data["fields"]
        }

    return GraphQLInterfaceType(
        name=type_data["name"],
        fields=thunk,
    )


def get_proxy_input_type(types_map, type_data):
    def thunk():
        return {
            field["name"]: GraphQLInputField(get_proxy_object_field(types_map, field["type"]))
            for field in type_data["inputFields"]
        }

    return GraphQLInputObjectType(
        type_data["name"],
        fields=thunk,
    )


def get_proxy_union_type(types_map, type_data):
    possible_types = [t["name"] for t in type_data["possibleTypes"]]

    def create_thunk(types_map, possible_types):
        def thunk():
            return [types_map[type_name] for type_name in possible_types]
        
        return thunk

    return GraphQLUnionType(
        name=type_data["name"],
        types=create_thunk(types_map, possible_types),
    )
