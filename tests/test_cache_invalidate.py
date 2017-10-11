import asyncio

import pytest

from async_lru import alru_cache

pytestmark = pytest.mark.asyncio


async def test_cache_invalidate(check_lru, loop):
    @alru_cache(loop=loop)
    async def coro(val):
        return val

    inputs = [1, 2, 3]

    coro.invalidate(1)
    coro.invalidate(2)
    coro.invalidate(3)

    coros = [coro(v) for v in inputs]

    ret = await asyncio.gather(*coros, loop=loop)

    assert ret == inputs
    check_lru(coro, hits=0, misses=3, cache=3, tasks=0)

    coro.invalidate(1)
    check_lru(coro, hits=0, misses=3, cache=2, tasks=0)
    coro.invalidate(2)
    check_lru(coro, hits=0, misses=3, cache=1, tasks=0)
    coro.invalidate(3)
    check_lru(coro, hits=0, misses=3, cache=0, tasks=0)

    inputs = [1, 2, 3]
    coros = [coro(v) for v in inputs]

    ret = await asyncio.gather(*coros, loop=loop)

    assert ret == inputs
    check_lru(coro, hits=0, misses=6, cache=3, tasks=0)
