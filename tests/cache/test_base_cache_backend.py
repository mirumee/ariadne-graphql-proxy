import pytest

from ariadne_graphql_proxy.cache import CacheBackend


@pytest.mark.asyncio
async def test_base_cache_backend_raises_not_implemented_for_set():
    cache = CacheBackend()

    with pytest.raises(NotImplementedError):
        await cache.set("key", "value")


@pytest.mark.asyncio
async def test_base_cache_backend_raises_not_implemented_for_get():
    cache = CacheBackend()

    with pytest.raises(NotImplementedError):
        await cache.get("key")


@pytest.mark.asyncio
async def test_base_cache_backend_raises_not_implemented_for_clear_all():
    cache = CacheBackend()

    with pytest.raises(NotImplementedError):
        await cache.clear_all()
