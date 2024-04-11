import pytest
from ariadne import make_executable_schema
from graphql import get_introspection_query, graphql_sync


@pytest.fixture
def schema():
    return make_executable_schema(
        """
        scalar Generic

        type Query {
            basic(arg: Generic, other: Generic): String
            complex(arg: Generic, other: Generic): Complex
            unionField: [DeliveryMethod!]!
        }

        type Complex {
            id: ID!
            name(arg: Generic, other: Generic): String!
            class(arg: Generic, other: Generic): String!
            group(arg: Generic, other: Generic): Group!
        }

        type Group {
            id(arg: Generic, other: Generic): ID!
            name(arg: Generic, other: Generic): String!
            rank(arg: Generic, other: Generic): Int!
        }

        input InputType {
            arg1: Float!
            arg2: Boolean!
            arg3: String!
            arg4: ID!
            arg5: Int!
        }

        union DeliveryMethod = Shipping | Warehouse

        type Shipping {
            id: ID!
            name: String!
        }

        type Warehouse {
            id: ID!
            address: String!
        }
        """
    )


@pytest.fixture
def schema_json(schema):
    schema_data = graphql_sync(schema, get_introspection_query()).data
    return {"data": schema_data}


@pytest.fixture
def other_schema():
    return make_executable_schema(
        """
        scalar Generic

        type Query {
            other(arg: Generic, other: Generic): String
            otherComplex(arg: Generic, other: Generic): OtherComplex
        }

        type OtherComplex {
            id: ID!
            name(arg: Generic, other: Generic): String!
            class(arg: Generic, other: Generic): String!
            group(arg: Generic, other: Generic): OtherGroup!
        }

        type OtherGroup {
            id(arg: Generic, other: Generic): ID!
            name(arg: Generic, other: Generic): String!
            rank(arg: Generic, other: Generic): Int!
        }
        """
    )


@pytest.fixture
def other_schema_json(other_schema):
    schema_data = graphql_sync(other_schema, get_introspection_query()).data
    return {"data": schema_data}


@pytest.fixture
def complex_schema():
    return make_executable_schema(
        """
        scalar Generic

        type Query {
            complex(arg: Generic, other: Generic): Complex
        }

        type Complex {
            id: ID!
        }
        """
    )


@pytest.fixture
def complex_schema_json(complex_schema):
    schema_data = graphql_sync(complex_schema, get_introspection_query()).data
    return {"data": schema_data}


@pytest.fixture
def root_value():
    return {
        "basic": "Lorem Ipsum",
        "complex": {
            "id": 123,
            "name": "Test Type",
            "class": "demo",
            "group": {
                "id": 321,
                "name": "Testing",
                "rank": 9001,
            },
        },
        "deliveryMethod": [
            {
                "__typename": "Shipping",
                "id": "SHIP:1",
                "name": "Test Shipping",
            },
            {
                "__typename": "Warehouse",
                "id": "WAREHOUSE:13",
                "address": "Warehouse #13",
            },
        ],
        "other": "Dolor Met",
        "otherComplex": {
            "id": 123,
            "name": "Test Type",
            "class": "demo",
            "group": {
                "id": 321,
                "name": "Testing",
                "rank": 9001,
            },
        },
    }


@pytest.fixture
def store_schema():
    return make_executable_schema(
        """
        type Query {
            order(id: ID!): Order
        }

        type Order {
            id: ID!
            customer: String!
            address: String!
            country: String!
        }

        type Mutation {
            login(username: String!, password: String!): String
            orderCreate(
                customer: String!
                address: String!
                country: String!
            ): OrderCreate!
        }

        type OrderCreate {
            order: Order
            errors: [String!]
        }
        """
    )


@pytest.fixture
def store_schema_json(store_schema):
    schema_data = graphql_sync(store_schema, get_introspection_query()).data
    return {"data": schema_data}


@pytest.fixture
def store_root_value():
    order = {
        "id": "5s87d6sa85f7asds",
        "customer": "John Doe",
        "address": "LongStrasse",
        "country": "Midgar",
    }

    return {
        "order": order,
        "orderCreate": {
            "order": order,
            "errors": None,
        },
    }


@pytest.fixture
def order_create_schema():
    return make_executable_schema(
        """
        type Query {
            noop: Boolean
        }

        type Order {
            id: ID!
        }

        type Mutation {
            orderCreate(
                customer: String!
                address: String!
                country: String!
            ): OrderCreate!
        }

        type OrderCreate {
            order: Order
            errors: [String!]
        }
        """
    )


@pytest.fixture
def order_create_schema_json(order_create_schema):
    schema_data = graphql_sync(order_create_schema, get_introspection_query()).data
    return {"data": schema_data}


@pytest.fixture
def order_create_root_value():
    order = {
        "id": "5s87d6sa85f7asds",
    }

    return {
        "order": order,
        "orderCreate": {
            "order": order,
            "errors": None,
        },
    }


@pytest.fixture
def search_schema():
    return make_executable_schema(
        """
        type Query {
            search(query: String!): [Result!]!
        }

        interface Result {
            id: ID!
            url: String!
        }

        type User implements Result {
            id: ID!
            url: String!
            username: String!
            email: String!
        }

        type Order implements Result {
            id: ID!
            url: String!
        }
        """
    )


@pytest.fixture
def search_schema_json(search_schema):
    schema_data = graphql_sync(search_schema, get_introspection_query()).data
    return {"data": schema_data}


@pytest.fixture
def search_root_value():
    return {
        "search": [
            {
                "__typename": "User",
                "url": "/u/aerith/3/",
                "id": "3",
                "username": "Aerith",
                "email": "aerith@example.com",
            },
            {
                "__typename": "Order",
                "id": "5s87d6sa85f7asds",
                "url": "/o/5s87d6sa85f7asds/",
            },
            {
                "__typename": "User",
                "url": "/u/bob/7/",
                "id": "7",
                "username": "Bob",
                "email": "bob@example.com",
            },
        ]
    }


@pytest.fixture
def gql():
    return lambda x: x


@pytest.fixture
def car_schema():
    return make_executable_schema(
        """
        type Query {
            carsByIds(ids: [ID!]!): [Car!]!
            carsByCriteria(input: SearchInput!): [Car!]!
        }

        type Car {
            id: ID!
            make: String!
            model: String!
            year: Int!
        }

        input SearchInput {
            search: SearchCriteria
        }

        input SearchCriteria {
            make: String
            model: String
            year: Int
        }
        """
    )


@pytest.fixture
def car_schema_json(car_schema):
    schema_data = graphql_sync(car_schema, get_introspection_query()).data
    return {"data": schema_data}


@pytest.fixture
def car_root_value():
    return {
        "carsByIds": [
            {"id": "car1", "make": "Toyota", "model": "Corolla", "year": 2020},
            {"id": "car2", "make": "Honda", "model": "Civic", "year": 2019},
        ],
        "carsByCriteria": [
            {"id": "car3", "make": "Ford", "model": "Mustang", "year": 2018},
            {"id": "car4", "make": "Chevrolet", "model": "Camaro", "year": 2017},
        ],
    }
