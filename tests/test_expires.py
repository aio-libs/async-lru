import asyncio

import pytest

from async_lru import alru_cache

pytestmark = pytest.mark.asyncio


async def test_expires(check_lru, loop):
    @alru_cache(maxsize=4, expires=0.2, loop=loop)
    async def coro(val):
        return val

    value = 1

    assert await coro(value) == value
    check_lru(coro, hits=0, misses=1, cache=1, tasks=0, maxsize=4)

    await asyncio.sleep(0.1, loop=loop)
    assert await coro(value) == value
    check_lru(coro, hits=1, misses=1, cache=1, tasks=0, maxsize=4)

    await asyncio.sleep(0.3, loop=loop)
    # cache is clear after time expires
    check_lru(coro, hits=1, misses=1, cache=0, tasks=0, maxsize=4)
    assert await coro(value) == value
    check_lru(coro, hits=1, misses=2, cache=1, tasks=0, maxsize=4)


async def test_expires_maxsize(check_lru, loop):
    @alru_cache(maxsize=1, expires=0.2, loop=loop)
    async def coro(val):
        return val

    assert await coro(1) == 1
    check_lru(coro, hits=0, misses=1, cache=1, tasks=0, maxsize=1)

    assert await coro(2) == 2
    check_lru(coro, hits=0, misses=2, cache=1, tasks=0, maxsize=1)

    await asyncio.sleep(0.1, loop=loop)
    assert await coro(2) == 2
    check_lru(coro, hits=1, misses=2, cache=1, tasks=0, maxsize=1)

    assert await coro(1) == 1
    check_lru(coro, hits=1, misses=3, cache=1, tasks=0, maxsize=1)
