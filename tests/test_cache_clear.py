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


async def test_cache_clear_pending_task() -> None:
    @alru_cache()
    async def coro() -> str:
        await asyncio.sleep(0.5)
        return "foo"

    t = asyncio.create_task(coro())
    await asyncio.sleep(0)
    assert len(coro._LRUCacheWrapper__tasks) == 1  # type: ignore[attr-defined]
    inner_task = next(iter(coro._LRUCacheWrapper__tasks))  # type: ignore[attr-defined]
    assert not inner_task.done()

    coro.cache_clear()
    await inner_task

    assert await t == "foo"
    assert inner_task.done()


async def test_cache_clear_ttl_callback(check_lru: Callable[..., None]) -> None:
    @alru_cache(ttl=0.5)
    async def coro() -> str:
        return "foo"

    await coro()
    assert len(coro._LRUCacheWrapper__cache) == 1  # type: ignore[attr-defined]
    cache_item = next(iter(coro._LRUCacheWrapper__cache.values()))  # type: ignore[attr-defined]
    assert not cache_item.later_call.cancelled()

    coro.cache_clear()

    assert cache_item.later_call.cancelled()
    await asyncio.sleep(0.5)
