import asyncio
from functools import _make_key
from typing import Callable

from async_lru import alru_cache


async def test_alru_cache_removing_lru_keys(check_lru: Callable[..., None]) -> None:
    @alru_cache(maxsize=3)
    async def coro(val: int) -> int:
        return val

    key5 = _make_key((5,), {}, False)
    key4 = _make_key((4,), {}, False)
    key3 = _make_key((3,), {}, False)
    key2 = _make_key((2,), {}, False)
    key1 = _make_key((1,), {}, False)

    for i, v in enumerate([3, 4, 5]):
        await coro(v)
        check_lru(coro, hits=0, misses=i + 1, cache=i + 1, tasks=0, maxsize=3)

    check_lru(coro, hits=0, misses=3, cache=3, tasks=0, maxsize=3)
    assert list(coro._LRUCacheWrapper__cache) == [key3, key4, key5]  # type: ignore[attr-defined]  # noqa: E501

    for v in [3, 2, 1]:
        await coro(v)
    check_lru(coro, hits=1, misses=5, cache=3, tasks=0, maxsize=3)
    assert list(coro._LRUCacheWrapper__cache) == [key3, key2, key1]  # type: ignore[attr-defined]  # noqa: E501


async def test_alru_cache_none_max_size(check_lru: Callable[..., None]) -> None:
    @alru_cache(maxsize=None)
    async def coro(val: int) -> int:
        return val

    inputs = [1, 2, 3, 4] * 2
    coros = [coro(v) for v in inputs]

    ret = await asyncio.gather(*coros)

    check_lru(coro, hits=4, misses=4, cache=4, tasks=0, maxsize=None)
    assert ret == inputs


async def test_alru_cache_zero_max_size(check_lru: Callable[..., None]) -> None:
    @alru_cache(maxsize=0)
    async def coro(val: int) -> int:
        return val

    inputs = [1, 2, 3, 4] * 2
    coros = [coro(v) for v in inputs]

    ret = await asyncio.gather(*coros)

    check_lru(coro, hits=0, misses=8, cache=0, tasks=0, maxsize=0)
    assert ret == inputs
