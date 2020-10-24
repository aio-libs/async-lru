import asyncio

import pytest

from async_lru import alru_cache


pytestmark = pytest.mark.asyncio


async def test_alru_cache_exception(check_lru, loop):
    @alru_cache(cache_exceptions=True)
    async def coro(val):
        1 / 0

    inputs = [1, 1, 1]
    coros = [coro(v) for v in inputs]

    ret = await asyncio.gather(*coros, return_exceptions=True)

    check_lru(coro, hits=2, misses=1, cache=1, tasks=0)

    for item in ret:
        assert isinstance(item, ZeroDivisionError)

    with pytest.raises(ZeroDivisionError):
        await coro(1)

    check_lru(coro, hits=3, misses=1, cache=1, tasks=0)


async def test_alru_not_cache_exception(check_lru, loop):
    @alru_cache(cache_exceptions=False)
    async def coro(val):
        1 / 0

    inputs = [1, 1, 1]
    coros = [coro(v) for v in inputs]

    ret = await asyncio.gather(*coros, return_exceptions=True)

    check_lru(coro, hits=2, misses=1, cache=1, tasks=0)

    for item in ret:
        assert isinstance(item, ZeroDivisionError)

    with pytest.raises(ZeroDivisionError):
        await coro(1)

    check_lru(coro, hits=2, misses=2, cache=1, tasks=0)
