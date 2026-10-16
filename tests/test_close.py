import asyncio
from collections.abc import Callable

import pytest

from async_lru import AlruCacheLoopResetWarning, alru_cache


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

    check_lru(coro, hits=0, misses=5, cache=0, tasks=0)
    assert coro.cache_parameters()["closed"]

    with pytest.raises(asyncio.CancelledError):
        await gather

    check_lru(coro, hits=0, misses=5, cache=0, tasks=0)
    assert coro.cache_parameters()["closed"]

    # double call is no-op
    await coro.cache_close()


async def test_cache_close_wait_bound_method(check_lru: Callable[..., None]) -> None:
    class Foo:
        @alru_cache()
        async def coro(self, val: int) -> int:
            await asyncio.sleep(0.02)
            return val

    foo = Foo()
    inputs = [1, 2, 3]

    coros = [foo.coro(v) for v in inputs]
    gather = asyncio.gather(*coros)

    # Yield to loop to start tasks
    await asyncio.sleep(0)

    # wait=True should allow tasks to finish (no cancellation)
    await foo.coro.cache_close(wait=True)

    results = await gather
    assert results == inputs

    check_lru(foo.coro, hits=0, misses=3, cache=3, tasks=0)
    assert foo.coro.cache_parameters()["closed"]


@pytest.mark.parametrize("removal", ("evict", "invalidate", "clear", "uncached"))
@pytest.mark.parametrize("wait", (False, True))
async def test_cache_close_detached_task(removal: str, wait: bool) -> None:
    started = asyncio.Event()
    release = asyncio.Event()
    finished = asyncio.Event()

    @alru_cache(maxsize=0 if removal == "uncached" else 1)
    async def coro(key: str) -> str:
        if key == "other":
            return key
        started.set()
        try:
            await release.wait()
            return key
        finally:
            finished.set()

    caller = asyncio.create_task(coro("key"))
    close = None
    try:
        await asyncio.wait_for(started.wait(), timeout=5)
        if removal == "evict":
            assert await coro("other") == "other"
        elif removal == "invalidate":
            assert coro.cache_invalidate("key")
        elif removal == "clear":
            coro.cache_clear()

        assert not coro.cache_contains("key")
        close = asyncio.create_task(coro.cache_close(wait=wait))
        if wait:
            await asyncio.sleep(0)
            assert not close.done()
            assert not finished.is_set()
            release.set()
            assert await asyncio.wait_for(caller, timeout=5) == "key"
        else:
            await asyncio.wait_for(close, timeout=5)
            assert finished.is_set()
            with pytest.raises(asyncio.CancelledError):
                await caller

        await asyncio.wait_for(close, timeout=5)
        assert coro.cache_parameters()["tasks"] == 0
        assert coro.cache_parameters()["closed"]
        await coro.cache_close(wait=wait)
    finally:
        release.set()
        await asyncio.gather(caller, return_exceptions=True)
        if close is not None:
            await close
        await coro.cache_close()


def test_cache_close_after_loop_reset_with_pending_task() -> None:
    started = asyncio.Event()
    release = asyncio.Event()

    @alru_cache()
    async def coro(key: str) -> str:
        if key == "old":
            started.set()
            await release.wait()
        return key

    old_loop = asyncio.new_event_loop()
    new_loop = asyncio.new_event_loop()
    caller = old_loop.create_task(coro("old"))
    try:
        old_loop.run_until_complete(asyncio.wait_for(started.wait(), timeout=5))
        assert coro.cache_parameters()["tasks"] == 1

        with pytest.warns(AlruCacheLoopResetWarning):
            assert new_loop.run_until_complete(coro("new")) == "new"

        assert coro.cache_parameters()["tasks"] == 0
        new_loop.run_until_complete(coro.cache_close(wait=True))
        assert not caller.done()
    finally:
        release.set()
        old_loop.run_until_complete(caller)
        old_loop.close()
        new_loop.close()
