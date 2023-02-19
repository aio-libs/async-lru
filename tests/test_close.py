import asyncio
from typing import Callable

import pytest

from async_lru import alru_cache


async def test_cache_close(check_lru: Callable[..., None]) -> None:
    @alru_cache()
    async def coro(val: int) -> int:
        await asyncio.sleep(0.2)

        return val

    assert not coro.cache_parameters()["closed"]

    inputs = [1, 2, 3, 4, 5]

    coros = [coro(v) for v in inputs]

    gather = asyncio.gather(*coros)

    await asyncio.sleep(0.1)

    check_lru(coro, hits=0, misses=5, cache=5, tasks=5)

    close = coro.cache_close()

    check_lru(coro, hits=0, misses=5, cache=5, tasks=5)

    await close

    check_lru(coro, hits=0, misses=5, cache=5, tasks=0)
    assert coro.cache_parameters()["closed"]

    with pytest.raises(asyncio.CancelledError):
        await gather

    check_lru(coro, hits=0, misses=5, cache=5, tasks=0)
    assert coro.cache_parameters()["closed"]

    # double call is no-op
    await coro.cache_close()
