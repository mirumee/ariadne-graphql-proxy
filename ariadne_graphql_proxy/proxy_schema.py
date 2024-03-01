from asyncio import gather
from functools import reduce
from inspect import isawaitable
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

from ariadne.types import BaseProxyRootValue, RootValue
from graphql import (
    DocumentNode,
    GraphQLInterfaceType,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLUnionType,
    GraphQLWrappingType,
    print_ast,
)
from httpx import AsyncClient

from .copy import copy_schema
from .merge import merge_schemas
from .proxy_root_value import ProxyRootValue
from .query_filter import QueryFilter
from .remote_schema import get_remote_schema
from .standard_types import STANDARD_TYPES, add_missing_scalar_types
from .str_to_field import (
    get_field_definition_from_str,
    get_graphql_field_from_field_definition,
)


ProxyHeaders = Union[dict, Callable[[Any], dict]]


class ProxySchema:
    def __init__(
        self,
        root_value: Optional[RootValue] = None,
        proxy_root_value: Type[ProxyRootValue] = ProxyRootValue,
    ):
        self.schemas: List[GraphQLSchema] = []
        self.urls: List[Optional[str]] = []
        self.headers: List[Optional[ProxyHeaders]] = []
        self.proxy_errors: List[bool] = []
        self.proxy_extensions: List[bool] = []
        self.labels: List[str] = []
        self.fields_map: Dict[str, Dict[str, Set[int]]] = {}
        self.fields_types: Dict[str, Dict[str, str]] = {}
        self.unions: Dict[str, List[str]] = {}
        self.foreign_keys: Dict[str, Dict[str, List[str]]] = {}

        self.proxy_root_value = proxy_root_value

        self.schema: Optional[GraphQLSchema] = None
        self.query_filter: Optional[QueryFilter] = None
        self.root_value: Optional[RootValue] = root_value

    def add_remote_schema(
        self,
        url: str,
        headers: Optional[ProxyHeaders] = None,
        *,
        exclude_types: Optional[List[str]] = None,
        exclude_args: Optional[Dict[str, Dict[str, List[str]]]] = None,
        exclude_fields: Optional[Dict[str, List[str]]] = None,
        exclude_directives: Optional[List[str]] = None,
        exclude_directives_args: Optional[Dict[str, List[str]]] = None,
        extra_fields: Optional[Dict[str, List[str]]] = None,
        label: Optional[str] = None,
        proxy_errors: bool = True,
        proxy_extensions: bool = True,
    ) -> int:
        if callable(headers):
            remote_schema = get_remote_schema(url, headers(None))
        else:
            remote_schema = get_remote_schema(url, headers)

        schema_id = len(self.schemas)

        return self.add_schema(
            remote_schema,
            url,
            headers,
            exclude_types=exclude_types,
            exclude_args=exclude_args,
            exclude_fields=exclude_fields,
            exclude_directives=exclude_directives,
            exclude_directives_args=exclude_directives_args,
            extra_fields=extra_fields,
            label=label or f"remote_{schema_id}",
            proxy_errors=proxy_errors,
            proxy_extensions=proxy_extensions,
        )

    def add_schema(
        self,
        schema: GraphQLSchema,
        url: Optional[str] = None,
        headers: Optional[ProxyHeaders] = None,
        *,
        exclude_types: Optional[List[str]] = None,
        exclude_args: Optional[Dict[str, Dict[str, List[str]]]] = None,
        exclude_fields: Optional[Dict[str, List[str]]] = None,
        exclude_directives: Optional[List[str]] = None,
        exclude_directives_args: Optional[Dict[str, List[str]]] = None,
        extra_fields: Optional[Dict[str, List[str]]] = None,
        label: Optional[str] = None,
        proxy_errors: bool = True,
        proxy_extensions: bool = True,
    ) -> int:
        if (
            exclude_types
            or exclude_args
            or exclude_fields
            or exclude_directives
            or exclude_directives_args
        ):
            schema = copy_schema(
                schema,
                exclude_types=exclude_types,
                exclude_args=exclude_args,
                exclude_fields=exclude_fields,
                exclude_directives=exclude_directives,
                exclude_directives_args=exclude_directives_args,
            )

        schema.type_map = add_missing_scalar_types(schema.type_map)

        schema_id = len(self.schemas)

        self.schemas.append(schema)
        self.urls.append(url)
        self.headers.append(headers)
        self.labels.append(label or f"schema_{schema_id}")
        self.proxy_errors.append(proxy_errors)
        self.proxy_extensions.append(proxy_extensions)

        for type_name, type_def in schema.type_map.items():
            if type_name in STANDARD_TYPES:
                continue

            if isinstance(type_def, GraphQLUnionType):
                self.unions[type_name] = [
                    object_type.name for object_type in type_def.types
                ]

            if not isinstance(type_def, (GraphQLInterfaceType, GraphQLObjectType)):
                continue

            if type_name not in self.fields_map:
                self.fields_map[type_name] = {}

            for field_name in type_def.fields:
                if field_name not in self.fields_map[type_name]:
                    self.fields_map[type_name][field_name] = set()

                self.fields_map[type_name][field_name].add(schema_id)

        if extra_fields:
            for type_name, type_fields in extra_fields.items():
                if type_name not in self.fields_map:
                    self.fields_map[type_name] = {}

                for field_name in type_fields:
                    if field_name not in self.fields_map[type_name]:
                        self.fields_map[type_name][field_name] = set()

                    self.fields_map[type_name][field_name].add(schema_id)

        return schema_id

    def add_foreign_key(
        self, type_name: str, field_name: str, on: Union[str, List[str]]
    ):
        if type_name not in self.foreign_keys:
            self.foreign_keys[type_name] = {}

        if field_name in self.foreign_keys[type_name]:
            raise ValueError(f"Foreign key already exists on {type_name}.{field_name}")

        self.foreign_keys[type_name][field_name] = [on] if isinstance(on, str) else on

    def add_delayed_fields(self, delayed_fields: Dict[str, List[str]]):
        for type_name, type_fields in delayed_fields.items():
            if type_name not in self.fields_map:
                continue

            for field_name in type_fields:
                self.fields_map[type_name].pop(field_name, None)

    def insert_field(self, type_name: str, field_str: str):
        field_definition = get_field_definition_from_str(field_str=field_str)
        field_name = field_definition.name.value
        for schema in self.schemas:
            type_ = schema.type_map.get(type_name)
            if not type_ or not hasattr(type_, "fields"):
                continue

            type_.fields[field_name] = get_graphql_field_from_field_definition(
                schema=schema, field_definition=field_definition
            )

    def get_sub_schema(self, schema_id: int) -> GraphQLSchema:
        try:
            return self.schemas[schema_id]
        except IndexError as exc:
            raise IndexError(f"Schema with ID {schema_id} doesn't exist") from exc

    def get_final_schema(self) -> GraphQLSchema:
        self.schema = reduce(merge_schemas, self.schemas[1:], self.schemas[0])

        for type_name, type_def in self.schema.type_map.items():
            if not isinstance(type_def, GraphQLObjectType):
                continue

            if type_name not in self.fields_types:
                self.fields_types[type_name] = {}

            for field_name in type_def.fields:
                field_type = type_def.fields[field_name].type
                while isinstance(field_type, GraphQLWrappingType):
                    field_type = field_type.of_type
                self.fields_types[type_name][field_name] = field_type.name

        self.query_filter = QueryFilter(
            self.schema,
            self.schemas,
            self.fields_map,
            self.fields_types,
            self.unions,
            self.foreign_keys,
        )

        return self.schema

    async def root_resolver(
        self,
        context_value: dict,
        operation_name: Optional[str],
        variables: Optional[dict],
        document: DocumentNode,
    ) -> Optional[dict]:
        if not self.query_filter:
            raise RuntimeError(
                "'get_final_schema' needs to be called to build final schema "
                "before `root_resolver` will be available to use."
            )

        context_value["root_query"] = {
            "operationName": operation_name,
            "document": document,
            "variables": variables,
        }

        queries = self.query_filter.split_query(document)

        if callable(self.root_value):
            root_value = self.root_value(
                context_value, operation_name, variables, document  # type: ignore
            )
            if isawaitable(root_value):
                root_value = await root_value
        elif self.root_value:
            root_value = self.root_value.copy()
        else:
            root_value = {}

        if not queries:
            return root_value

        root_errors: List[dict] = []
        root_extensions: dict = {}

        subqueries_data = await gather(
            *[
                self.fetch_data(
                    schema_id,
                    context_value,
                    self.urls[schema_id],
                    self.headers[schema_id],
                    {
                        "operationName": operation_name,
                        "query": print_ast(query_document),
                        "variables": (
                            {
                                key: variables[key]
                                for key in query_variables
                                if key in variables
                            }
                            if variables
                            else None
                        ),
                    },
                )
                for schema_id, query_document, query_variables in queries
                if self.urls[schema_id]
            ]
        )

        for schema_id, subquery_data in subqueries_data:
            label = self.labels[schema_id]
            if isinstance(subquery_data.get("data"), dict):
                root_value.update(subquery_data["data"])
            if (
                isinstance(subquery_data.get("errors"), list)
                and self.proxy_errors[schema_id]
            ):
                root_errors += self.clean_errors(label, subquery_data["errors"])
            if (
                isinstance(subquery_data.get("extensions"), dict)
                and self.proxy_extensions[schema_id]
            ):
                root_extensions[label] = subquery_data["extensions"]

        if root_errors or root_extensions:
            return self.proxy_root_value(
                root_value,
                root_errors or None,
                root_extensions or None,
            )

        return root_value or None

    async def fetch_data(self, schema_id, context, url, headers, json):
        async with AsyncClient() as client:
            if callable(headers):
                headers = headers(context)

            r = await client.post(
                url,
                headers=headers,
                json=json,
            )

            query_data = r.json()
            return (schema_id, query_data)

    def clean_errors(self, label: str, errors: List[dict]) -> List[dict]:
        clean_errors: List[dict] = []
        for error in errors:
            if isinstance(error, dict) and isinstance(error.get("path"), list):
                error["path"].insert(0, label)
                clean_errors.append(error)
        return clean_errors
