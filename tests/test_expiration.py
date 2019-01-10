import asyncio
import time

import pytest

from async_lru import alru_cache

pytestmark = pytest.mark.asyncio


async def test_expiration(check_lru, loop):
    @alru_cache(maxsize=4, expiration_time=2, loop=loop)
    async def coro(val):
        return val

    inputs = [1, 2, 3]
    coros = [coro(v) for v in inputs]
    ret = await asyncio.gather(*coros, loop=loop)
    assert ret == inputs
    check_lru(coro, hits=0, misses=3, cache=3, tasks=0, maxsize=4)

    time.sleep(1)
    inputs = 1
    ret = await coro(inputs)
    assert ret == inputs
    check_lru(coro, hits=1, misses=3, cache=3, tasks=0, maxsize=4)

    time.sleep(3)
    inputs = 1
    ret = await coro(inputs)
    assert ret == inputs
    check_lru(coro, hits=1, misses=4, cache=3, tasks=0, maxsize=4)
