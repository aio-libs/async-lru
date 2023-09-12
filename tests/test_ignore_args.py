import asyncio
from typing import Callable

import pytest

from async_lru import alru_cache


async def test_ignore_args_cache(check_lru: Callable[..., None]) -> None:
    @alru_cache(maxsize=None, ignore_args=['val1'])
    async def coro(val1: int, val2: int) -> int:
        return val1 + val2

    assert await coro(1, 2) == 3
    check_lru(coro, hits=0, misses=1, cache=1, tasks=0, maxsize=None)
    await asyncio.sleep(0.0)
    # since we are ignoring val1, it should return the previous cached result (3)
    assert await coro(2, 2) == 3
    check_lru(coro, hits=1, misses=1, cache=1, tasks=0, maxsize=None)


async def test_ignore_args_kwargs_cache(check_lru: Callable[..., None]) -> None:
    @alru_cache(maxsize=None, ignore_args=['val1'])
    async def coro(val1: int, val2: int) -> int:
        return val1 + val2

    assert await coro(val2=2, val1=1) == 3
    check_lru(coro, hits=0, misses=1, cache=1, tasks=0, maxsize=None)
    await asyncio.sleep(0.0)
    # since we are ignoring val1, it should return the previous cached result (3)
    assert await coro(val2=2, val1=2) == 3
    check_lru(coro, hits=1, misses=1, cache=1, tasks=0, maxsize=None)

async def test_ignore_args_arg_does_not_exist(check_lru: Callable[..., None]) -> None:
    with pytest.raises(ValueError):
        @alru_cache(ignore_args=["asd"])
        async def coro(val: int) -> int:
            return val
