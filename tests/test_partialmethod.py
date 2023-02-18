import asyncio
from functools import partial, partialmethod
from typing import Callable

from async_lru import alru_cache


async def test_partialmethod_basic(check_lru: Callable[..., None]) -> None:
    class Obj:
        async def _coro(self, val: int) -> int:
            return val

        coro = alru_cache(partialmethod(_coro, 2))

    obj = Obj()

    coros = [obj.coro() for _ in range(5)]

    check_lru(obj.coro, hits=0, misses=0, cache=0, tasks=0)

    ret = await asyncio.gather(*coros)

    check_lru(obj.coro, hits=4, misses=1, cache=1, tasks=0)

    assert ret == [2, 2, 2, 2, 2]


async def test_partialmethod_partial(check_lru: Callable[..., None]) -> None:
    class Obj:
        def __init__(self) -> None:
            self.coro = alru_cache(partial(self._coro, 2))

        async def __coro(self, val1: int, val2: int) -> int:
            return val1 + val2

        _coro = partialmethod(__coro, 1)

    obj = Obj()

    coros = [obj.coro() for _ in range(5)]

    check_lru(obj.coro, hits=0, misses=0, cache=0, tasks=0)

    ret = await asyncio.gather(*coros)

    check_lru(obj.coro, hits=4, misses=1, cache=1, tasks=0)

    assert ret == [3, 3, 3, 3, 3]
