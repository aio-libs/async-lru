import asyncio
from typing import Callable

from async_lru import alru_cache


async def test_cache_clear(check_lru: Callable[..., None]) -> None:
    @alru_cache()
    async def coro(val: int) -> int:
        return val

    inputs = [1, 2, 3]
    coros = [coro(v) for v in inputs]
    ret = await asyncio.gather(*coros)
    assert ret == inputs
    check_lru(coro, hits=0, misses=3, cache=3, tasks=0)

    coro.cache_clear()

    check_lru(coro, hits=0, misses=0, cache=0, tasks=0)
