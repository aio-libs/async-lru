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


async def test_cache_invalidate_multiple_args(check_lru, loop):
    @alru_cache(loop=loop)
    async def coro(*args):
        return len(args)

    for i, size in enumerate(range(10)):
        args = tuple(range(size))
        ret = await coro(*args)
        assert ret == size
        check_lru(coro, hits=0, misses=i+1, cache=1, tasks=0)
        coro.invalidate(*args)
        check_lru(coro, hits=0, misses=i+1, cache=0, tasks=0)

    for size in range(10):
        args = tuple(range(size))
        ret = await coro(*args)
        assert ret == size
    check_lru(coro, hits=0, misses=20, cache=10, tasks=0)


async def test_cache_invalidate_multiple_args_different_order(check_lru, loop):
    @alru_cache(loop=loop)
    async def coro(*args):
        return len(args)

    for i, size in enumerate(range(2, 10)):
        args = tuple(range(size))
        rev_args = tuple(reversed(args))
        ret = await coro(*args)
        assert ret == size
        check_lru(coro, hits=0, misses=2*i+1, cache=i+1, tasks=0)
        ret = await coro(*rev_args)
        # The reversed args should be a miss
        check_lru(coro, hits=0, misses=2*i+2, cache=i+2, tasks=0)
        coro.invalidate(*rev_args)
        # The reversed args should be invalidated
        check_lru(coro, hits=0, misses=2*i+2, cache=i+1, tasks=0)

    for i, size in enumerate(range(2, 10)):
        args = tuple(range(size))
        ret = await coro(*args)
        assert ret == size
        check_lru(coro, hits=i+1, misses=16, cache=8, tasks=0)
