from typing import Any

try:
    import orjson as json

    USING_ORJSON = True
except ImportError:
    import json  # type: ignore[no-redef]

    USING_ORJSON = False


class CacheSerializer:
    def serialize(self, value: Any) -> str:
        raise NotImplementedError(
            "Cache serializer needs to define custom 'serialize' method."
        )

    def deserialize(self, value: str) -> Any:
        raise NotImplementedError(
            "Cache serializer needs to define custom 'deserialize' method."
        )


class NoopCacheSerializer(CacheSerializer):
    def serialize(self, value: Any) -> str:
        return value

    def deserialize(self, value: str) -> Any:
        return value


class JSONCacheSerializer(CacheSerializer):
    def serialize(self, value: Any) -> str:
        if USING_ORJSON:
            return json.dumps(value).decode()

        return json.dumps(value)  # type: ignore

    def deserialize(self, value: str) -> Any:
        return json.loads(value)
