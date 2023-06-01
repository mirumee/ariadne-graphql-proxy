import asyncio

import pytest


from ariadne_graphql_proxy.cache import InMemoryCache


@pytest.mark.asyncio
async def test_value_is_cached_and_retrieved_from_memory():
    cache = InMemoryCache()
    await cache.set("key", 42)
    assert await cache.get("key") == 42


@pytest.mark.asyncio
async def test_none_is_returned_if_cache_key_is_not_set():
    cache = InMemoryCache()
    assert await cache.get("key") is None


@pytest.mark.asyncio
async def test_default_is_returned_if_cache_key_is_not_set():
    cache = InMemoryCache()
    assert await cache.get("key", "default") == "default"


@pytest.mark.asyncio
async def test_clear_all_empties_cache_memory():
    cache = InMemoryCache()
    await cache.set("key", 42)
    assert await cache.get("key") == 42

    await cache.clear_all()

    assert await cache.get("key") is None


@pytest.mark.asyncio
async def test_live_key_with_ttl_is_retrieved_from_memory():
    cache = InMemoryCache()
    await cache.set("key", 42, ttl=1)
    assert await cache.get("key") == 42

    await asyncio.sleep(1)
    assert await cache.get("key") is None


@pytest.mark.asyncio
async def test_default_is_returned_if_cache_key_is_expired():
    cache = InMemoryCache()
    await cache.set("key", 42, ttl=1)
    assert await cache.get("key") == 42

    await asyncio.sleep(1)
    assert await cache.get("key") is None
