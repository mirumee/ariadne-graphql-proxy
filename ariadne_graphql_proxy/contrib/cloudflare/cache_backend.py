import json
from typing import Any, Dict, Optional

import httpx

from ...cache import CacheBackend


class CloudflareCacheError(Exception):
    def __init__(self, response: httpx.Response) -> None:
        self.response = response
        msg = (
            "Namespace can't be accessed.\n"
            f"url: {response.url}\n"
            f"status: {response.status_code}\n"
            f"content: {response.content!r}"
        )
        super().__init__(msg)


class CloudflareCacheBackend(CacheBackend):
    def __init__(
        self,
        account_id: str,
        namespace_id: str,
        headers: Optional[Dict[str, str]] = None,
        base_url: str = "https://api.cloudflare.com/client/v4",
    ) -> None:
        self.base_url = base_url
        self.account_id = account_id
        self.namespace_id = namespace_id
        self.headers = headers or {}

        self._assert_namespace_can_be_accessed()

    def _assert_namespace_can_be_accessed(self):
        with httpx.Client(base_url=self.base_url, headers=self.headers) as client:
            response = client.get(
                f"accounts/{self.account_id}/"
                f"storage/kv/namespaces/{self.namespace_id}/keys"
            )

        if not response.is_success or not response.json().get("success", False):
            raise CloudflareCacheError(response)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        async with httpx.AsyncClient(
            base_url=self.base_url, headers=self.headers
        ) as client:
            await client.put(
                f"accounts/{self.account_id}/"
                f"storage/kv/namespaces/{self.namespace_id}/"
                f"values/{key}",
                files={"value": json.dumps({"value": value}), "metadata": "{}"},
                params={"expiration_ttl": ttl} if ttl is not None else {},
            )

    async def get(self, key: str, default: Any = None) -> Any:
        async with httpx.AsyncClient(
            base_url=self.base_url, headers=self.headers
        ) as client:
            response = await client.get(
                f"accounts/{self.account_id}/"
                f"storage/kv/namespaces/{self.namespace_id}/"
                f"values/{key}",
            )

        if response.is_success:
            return response.json()["value"]

        return default

    async def clear_all(self):
        pass
