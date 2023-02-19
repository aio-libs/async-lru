from typing import Callable

import pytest

from async_lru import alru_cache


async def test_alru_cache_open(check_lru: Callable[..., None]) -> None:
    @alru_cache()
    async def coro(val: int) -> int:
        return val

    await coro(1)

    check_lru(coro, hits=0, misses=1, cache=1, tasks=0)

    with pytest.raises(RuntimeError):
        coro.cache_open()

    close = coro.cache_close()

    assert coro.cache_parameters()["closed"]

    with pytest.raises(RuntimeError):
        await coro()

    with pytest.raises(RuntimeError):
        coro.cache_open()

    await close

    check_lru(coro, hits=0, misses=0, cache=0, tasks=0)

    coro.cache_open()

    ret = await coro(1)

    assert ret == 1

    check_lru(coro, hits=0, misses=1, cache=1, tasks=0)
