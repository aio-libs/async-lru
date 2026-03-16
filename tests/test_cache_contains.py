import asyncio
from typing import Callable

from async_lru import alru_cache


async def test_cache_contains_basic(check_lru: Callable[..., None]) -> None:
    @alru_cache(maxsize=4)
    async def coro(val):
        return val

    assert coro.cache_contains(1) is False
    await coro(1)
    assert coro.cache_contains(1) is True
    assert coro.cache_contains(2) is False
    check_lru(coro, hits=0, misses=1, cache=1, tasks=0, maxsize=4)


async def test_cache_contains_does_not_affect_counters(
    check_lru: Callable[..., None],
) -> None:
    @alru_cache(maxsize=4)
    async def coro(val):
        return val

    await coro(1)
    for _ in range(10):
        coro.cache_contains(1)
        coro.cache_contains(99)

    # hits/misses must stay unchanged after cache_contains calls
    check_lru(coro, hits=0, misses=1, cache=1, tasks=0, maxsize=4)


async def test_cache_contains_does_not_change_lru_order() -> None:
    @alru_cache(maxsize=2)
    async def coro(val):
        return val

    await coro(1)
    await coro(2)

    # Peek at key 1 without refreshing its LRU position
    assert coro.cache_contains(1) is True

    # Adding a third entry must evict key 1 (oldest), not key 2
    await coro(3)

    assert coro.cache_contains(1) is False
    assert coro.cache_contains(2) is True
    assert coro.cache_contains(3) is True


async def test_cache_contains_after_invalidate_and_clear() -> None:
    @alru_cache(maxsize=4)
    async def coro(val):
        return val

    await coro(1)
    await coro(2)

    coro.cache_invalidate(1)
    assert coro.cache_contains(1) is False
    assert coro.cache_contains(2) is True  # unaffected

    coro.cache_clear()
    assert coro.cache_contains(2) is False


async def test_cache_contains_with_kwargs() -> None:
    @alru_cache(maxsize=4)
    async def coro(a, b=10):
        return a + b

    await coro(1, b=20)
    assert coro.cache_contains(1, b=20) is True
    assert coro.cache_contains(1, b=30) is False
    assert coro.cache_contains(1) is False


async def test_cache_contains_respects_typed_flag() -> None:
    @alru_cache(maxsize=4, typed=True)
    async def coro(val):
        return val

    await coro(1)
    assert coro.cache_contains(1) is True
    assert coro.cache_contains(1.0) is False


async def test_cache_contains_pending_task() -> None:
    event = asyncio.Event()

    @alru_cache(maxsize=4)
    async def coro(val):
        await event.wait()
        return val

    task = asyncio.ensure_future(coro(1))
    await asyncio.sleep(0)

    # Key must be present even while the underlying task is still running
    assert coro.cache_contains(1) is True

    event.set()
    await task


async def test_cache_contains_after_ttl_expiry() -> None:
    @alru_cache(maxsize=4, ttl=0.05)
    async def coro(val):
        return val

    await coro(1)
    assert coro.cache_contains(1) is True

    await asyncio.sleep(0.1)
    assert coro.cache_contains(1) is False


async def test_cache_contains_on_method() -> None:
    class MyService:
        @alru_cache(maxsize=4)
        async def fetch(self, key):
            return key * 2

    svc = MyService()
    await svc.fetch(5)

    assert svc.fetch.cache_contains(5) is True
    assert svc.fetch.cache_contains(6) is False
