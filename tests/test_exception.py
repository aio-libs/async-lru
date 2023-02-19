import asyncio
from typing import Callable

import pytest

from async_lru import alru_cache


async def test_alru_exception(check_lru: Callable[..., None]) -> None:
    @alru_cache()
    async def coro(val: int) -> None:
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
