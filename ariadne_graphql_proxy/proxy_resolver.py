from httpx import AsyncClient


def setup_root_resolver(server_url: str):
    async def proxy_root_resolver(context_value, document):
        request = context_value["request"]
        request_json = await request.json()

        async with AsyncClient() as client:
            r = await client.post(
                server_url,
                json={
                    "operationName": request_json.get("operationName"),
                    "query": request_json.get("query"),
                    "variables": request_json.get("variables"),
                },
            )

            data = r.json()

        return data["data"]

    return proxy_root_resolver
