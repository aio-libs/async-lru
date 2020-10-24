import asyncio
from functools import partial, partialmethod

import pytest

from async_lru import alru_cache


pytestmark = pytest.mark.asyncio


async def test_partialmethod_basic(check_lru, loop):
    class Obj:
        async def _coro(self, val):
            return val

        coro = alru_cache(partialmethod(_coro, 2))

    obj = Obj()

    coros = [obj.coro() for _ in range(5)]

    check_lru(obj.coro, hits=0, misses=0, cache=0, tasks=0)

    ret = await asyncio.gather(*coros, loop=loop)

    check_lru(obj.coro, hits=4, misses=1, cache=1, tasks=0)

    assert ret == [2, 2, 2, 2, 2]


async def test_partialmethod_partial(check_lru, loop):
    class Obj:
        def __init__(self):
            self.coro = alru_cache(partial(self._coro, 2))

        async def __coro(self, val1, val2):
            return val1 + val2

        _coro = partialmethod(__coro, 1)

    obj = Obj()

    coros = [obj.coro() for _ in range(5)]

    check_lru(obj.coro, hits=0, misses=0, cache=0, tasks=0)

    ret = await asyncio.gather(*coros, loop=loop)

    check_lru(obj.coro, hits=4, misses=1, cache=1, tasks=0)

    assert ret == [3, 3, 3, 3, 3]


async def test_partialmethod_cls_loop(check_lru, loop):
    class Obj:
        def __init__(self, loop):
            self._loop = loop

        async def _coro(self, val):
            return val

        coro = alru_cache(partialmethod(_coro, 2))

    obj = Obj(loop=loop)

    coros = [obj.coro() for _ in range(5)]

    check_lru(obj.coro, hits=0, misses=0, cache=0, tasks=0)

    ret = await asyncio.gather(*coros, loop=loop)

    check_lru(obj.coro, hits=4, misses=1, cache=1, tasks=0)

    assert ret == [2, 2, 2, 2, 2]


async def test_partialmethod_kwargs_loop(check_lru, loop):
    class Obj:
        async def _coro(self, val, *, _loop):
            return val

        coro = alru_cache(partialmethod(_coro, 2))

    obj = Obj()

    coros = [obj.coro(_loop=loop) for _ in range(5)]

    check_lru(obj.coro, hits=0, misses=0, cache=0, tasks=0)

    ret = await asyncio.gather(*coros, loop=loop)

    check_lru(obj.coro, hits=4, misses=1, cache=1, tasks=0)

    assert ret == [2, 2, 2, 2, 2]
