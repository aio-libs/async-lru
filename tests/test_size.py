import asyncio

import pytest

from async_lru import _CacheInfo, _make_key, alru_cache

pytestmark = pytest.mark.asyncio


async def test_alru_cache_removing_lru_keys(loop):
    @alru_cache(maxsize=3, loop=loop)
    async def coro(val):
        return val

    key5 = _make_key((5,), {}, False)
    key4 = _make_key((4,), {}, False)
    key3 = _make_key((3,), {}, False)
    key2 = _make_key((2,), {}, False)
    key1 = _make_key((1,), {}, False)

    for v in [3, 4, 5]:
        await coro(v)
    assert len(coro._cache) == 3
    assert list(coro._cache) == [key3, key4, key5]

    for v in [3, 2, 1]:
        await coro(v)
    assert len(coro._cache) == 3
    assert list(coro._cache) == [key3, key2, key1]


async def test_alru_cache_none_max_size(loop):
    @alru_cache(maxsize=None, loop=loop)
    async def coro(val):
        return val

    inputs = [1, 2, 3, 4] * 2
    coros = [coro(v) for v in inputs]

    ret = await asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=4,
        misses=4,
        maxsize=None,
        currsize=4,
    )
    assert coro.cache_info() == expected
    assert len(coro._cache) == len(inputs) // 2
    assert len(coro.tasks) == 0
    assert ret == inputs


async def test_alru_cache_zero_max_size(loop):
    @alru_cache(maxsize=0, loop=loop)
    async def coro(val):
        return val

    inputs = [1, 2, 3, 4] * 2
    coros = [coro(v) for v in inputs]

    ret = await asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=0,
        misses=8,
        maxsize=0,
        currsize=0,
    )
    assert coro.cache_info() == expected
    assert len(coro._cache) == 0
    assert len(coro.tasks) == 0
    assert ret == inputs
