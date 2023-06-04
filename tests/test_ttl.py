import asyncio
from typing import Callable

from async_lru import alru_cache


async def test_ttl_infinite_cache(check_lru: Callable[..., None]) -> None:
    @alru_cache(maxsize=None, ttl=0.1)
    async def coro(val: int) -> int:
        return val

    assert await coro(1) == 1
    check_lru(coro, hits=0, misses=1, cache=1, tasks=0, maxsize=None)
    await asyncio.sleep(0.0)
    assert await coro(1) == 1
    check_lru(coro, hits=1, misses=1, cache=1, tasks=0, maxsize=None)

    await asyncio.sleep(0.2)
    # cache is clear after ttl expires
    check_lru(coro, hits=1, misses=1, cache=0, tasks=0, maxsize=None)
    assert await coro(1) == 1
    check_lru(coro, hits=1, misses=2, cache=1, tasks=0, maxsize=None)


async def test_ttl_limited_cache(check_lru: Callable[..., None]) -> None:
    @alru_cache(maxsize=1, ttl=0.1)
    async def coro(val: int) -> int:
        return val

    assert await coro(1) == 1
    check_lru(coro, hits=0, misses=1, cache=1, tasks=0, maxsize=1)

    assert await coro(2) == 2
    check_lru(coro, hits=0, misses=2, cache=1, tasks=0, maxsize=1)

    await asyncio.sleep(0)
    assert await coro(2) == 2
    check_lru(coro, hits=1, misses=2, cache=1, tasks=0, maxsize=1)

    assert await coro(1) == 1
    check_lru(coro, hits=1, misses=3, cache=1, tasks=0, maxsize=1)


async def test_ttl_with_explicit_invalidation(check_lru: Callable[..., None]) -> None:
    @alru_cache(maxsize=None, ttl=0.2)
    async def coro(val: int) -> int:
        return val

    assert await coro(1) == 1
    check_lru(coro, hits=0, misses=1, cache=1, tasks=0, maxsize=None)
    coro.cache_invalidate(1)
    check_lru(coro, hits=0, misses=1, cache=0, tasks=0, maxsize=None)
    await asyncio.sleep(0.1)
    assert await coro(1) == 1
    check_lru(coro, hits=0, misses=2, cache=1, tasks=0, maxsize=None)

    await asyncio.sleep(0.1)
    # cache is not cleared after ttl expires because invalidate also should clear
    # the invalidation by timeout
    check_lru(coro, hits=0, misses=2, cache=1, tasks=0, maxsize=None)


async def test_ttl_concurrent() -> None:
    @alru_cache(maxsize=1, ttl=1)
    async def coro(val: int) -> int:
        return val

    results = await asyncio.gather(*(coro(i) for i in range(2)))
    assert results == list(range(2))
