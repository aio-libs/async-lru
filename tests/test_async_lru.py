import asyncio

import pytest
from async_lru import _CacheInfo, _make_key, alru_cache

pytestmark = pytest.mark.asyncio


async def test_alru_cache_info(loop):
    @alru_cache(maxsize=4, loop=loop)
    async def coro(val):
        return val

    inputs = [1, 2, 3]
    coros = [coro(v) for v in inputs]
    ret = await asyncio.gather(*coros, loop=loop)
    assert ret == inputs
    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=4,
        currsize=3,
    )
    assert coro.cache_info() == expected

    coro.cache_clear()
    expected = _CacheInfo(
        hits=0,
        misses=0,
        maxsize=4,
        currsize=0,
    )
    assert coro.cache_info() == expected
    inputs = [1, 1, 1]
    coros = [coro(v) for v in inputs]
    ret = await asyncio.gather(*coros, loop=loop)
    assert ret == inputs
    expected = _CacheInfo(
        hits=2,
        misses=1,
        maxsize=4,
        currsize=1,
    )
    assert coro.cache_info() == expected

    coro.cache_clear()
    expected = _CacheInfo(
        hits=0,
        misses=0,
        maxsize=4,
        currsize=0,
    )
    assert coro.cache_info() == expected
    inputs = [1, 2, 3, 4] * 2
    coros = [coro(v) for v in inputs]
    ret = await asyncio.gather(*coros, loop=loop)
    assert ret == inputs
    expected = _CacheInfo(
        hits=4,
        misses=4,
        maxsize=4,
        currsize=4,
    )
    assert coro.cache_info() == expected


async def test_alru_cache_await_same(loop):
    calls = 0
    val = object()

    @alru_cache(loop=loop)
    async def coro():
        nonlocal calls
        calls += 1

        return val

    coros = [coro() for _ in range(20)]
    ret = await asyncio.gather(*coros, loop=loop)
    expected = [val] * 20
    assert ret == expected
    assert calls == 1
    assert await coro() is val


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
