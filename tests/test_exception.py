import asyncio

import pytest

from async_lru import alru_cache

pytestmark = pytest.mark.asyncio


async def test_alru_cache_exception(loop):
    @alru_cache(cache_exceptions=True, loop=loop)
    async def coro(val):
        1/0

    inputs = [1, 1, 1]
    coros = [coro(v) for v in inputs]

    ret = await asyncio.gather(*coros, loop=loop, return_exceptions=True)

    assert len(coro._cache) == 1
    assert len(coro.tasks) == 0
    assert coro.hits == 2
    assert coro.misses == 1

    for item in ret:
        assert isinstance(item, ZeroDivisionError)

    with pytest.raises(ZeroDivisionError):
        await coro(1)

    assert coro.hits == 3
    assert coro.misses == 1


async def test_alru_not_cache_exception(loop):
    @alru_cache(cache_exceptions=False, loop=loop)
    async def coro(val):
        1/0

    inputs = [1, 1, 1]
    coros = [coro(v) for v in inputs]

    ret = await asyncio.gather(*coros, loop=loop, return_exceptions=True)

    assert len(coro._cache) == 1
    assert len(coro.tasks) == 0
    assert coro.hits == 2
    assert coro.misses == 1

    for item in ret:
        assert isinstance(item, ZeroDivisionError)

    with pytest.raises(ZeroDivisionError):
        await coro(1)

    assert coro.hits == 2
    assert coro.misses == 2
