import time
from typing import Any, Optional

from ariadne_graphql_proxy.cache import CacheBackend

try:
    from asgiref.sync import sync_to_async
    from boto3.dynamodb.conditions import Attr, Key
    from boto3.session import Session
except ImportError as import_exc:
    raise ImportError(
        "DynamoDBCacheBackend requires 'boto3' and 'asgiref' packages."
    ) from import_exc


class DynamoDBCacheError(Exception):
    """Exception thrown by DynamoDBCacheBackend."""


class DynamoDBCacheBackend(CacheBackend):
    def __init__(
        self,
        table_name: str,
        partition_key: str = "key",
        ttl_attribute: str = "ttl",
        session: Optional[Session] = None,
    ) -> None:
        self.table_name = table_name
        self.partition_key = partition_key
        self.ttl_attribute = ttl_attribute
        self.value_attribute_name = "value"

        self.session = session if session else Session()
        self.dynamodb_resource = self.session.resource("dynamodb")
        self.table = self.dynamodb_resource.Table(self.table_name)

        self._assert_table_exists()

    def _assert_table_exists(self):
        not_found_exception = (
            self.dynamodb_resource.meta.client.exceptions.ResourceNotFoundException
        )
        try:
            self.table.table_status
        except not_found_exception as exc:
            raise DynamoDBCacheError(
                f'Unable to access "{self.table_name}" table.'
            ) from exc

    @sync_to_async
    def _put_item(self, item: dict):
        self.table.put_item(Item=item)

    @sync_to_async
    def _query_by_key(self, key: str, max_ttl: int) -> dict:
        return self.table.query(
            KeyConditionExpression=Key(self.partition_key).eq(key),
            FilterExpression=Attr(self.ttl_attribute).gte(max_ttl)
            | Attr(self.ttl_attribute).not_exists(),
        )

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        item = {self.partition_key: key, self.value_attribute_name: value}
        if ttl:
            now = int(time.time())
            item[self.ttl_attribute] = now + ttl

        await self._put_item(item=item)

    async def get(self, key: str, default: Any = None) -> Any:
        response = await self._query_by_key(key=key, max_ttl=int(time.time()))

        items = response.get("Items", [])
        if len(items) < 1:
            return default

        return items[0].get(self.value_attribute_name, default)

    async def clear_all(self):
        pass
