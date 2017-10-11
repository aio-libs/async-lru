import asyncio

import pytest

from async_lru import alru_cache

pytestmark = pytest.mark.asyncio


async def test_cache_info(check_lru, loop):
    @alru_cache(maxsize=4, loop=loop)
    async def coro(val):
        return val

    inputs = [1, 2, 3]
    coros = [coro(v) for v in inputs]
    ret = await asyncio.gather(*coros, loop=loop)
    assert ret == inputs
    check_lru(coro, hits=0, misses=3, cache=3, tasks=0, maxsize=4)

    coro.cache_clear()

    check_lru(coro, hits=0, misses=0, cache=0, tasks=0, maxsize=4)

    inputs = [1, 1, 1]
    coros = [coro(v) for v in inputs]
    ret = await asyncio.gather(*coros, loop=loop)
    assert ret == inputs
    check_lru(coro, hits=2, misses=1, cache=1, tasks=0, maxsize=4)

    coro.cache_clear()

    check_lru(coro, hits=0, misses=0, cache=0, tasks=0, maxsize=4)

    inputs = [1, 2, 3, 4] * 2
    coros = [coro(v) for v in inputs]
    ret = await asyncio.gather(*coros, loop=loop)
    assert ret == inputs
    check_lru(coro, hits=4, misses=4, cache=4, tasks=0, maxsize=4)
