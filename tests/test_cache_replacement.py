import asyncio
from unittest import mock

import pytest

from async_lru import alru_cache


@pytest.mark.parametrize("removal", ("invalidate", "clear", "evict"))
@pytest.mark.parametrize("outcome", ("result", "error", "cancel", "cancel_waiter"))
async def test_old_task_does_not_modify_replacement(removal: str, outcome: str) -> None:
    started = [asyncio.Event(), asyncio.Event()]
    release = [asyncio.Event(), asyncio.Event()]
    calls = 0

    @alru_cache(maxsize=1, ttl=60)
    async def cached(key: str) -> int:
        nonlocal calls
        if key == "other":
            return -1
        index = calls
        calls += 1
        started[index].set()
        await release[index].wait()
        if index == 0:
            if outcome == "error":
                raise RuntimeError("old task failed")
            if outcome == "cancel":
                raise asyncio.CancelledError
        return index

    old = asyncio.create_task(cached("key"))
    replacement = None
    try:
        await started[0].wait()
        if removal == "invalidate":
            assert cached.cache_invalidate("key")
        elif removal == "clear":
            cached.cache_clear()
        else:
            assert await cached("other") == -1

        replacement = asyncio.create_task(cached("key"))
        await started[1].wait()
        loop = asyncio.get_running_loop()
        with mock.patch.object(loop, "call_later", wraps=loop.call_later) as call_later:
            if outcome == "cancel_waiter":
                old.cancel()
            else:
                release[0].set()
            if outcome == "error":
                with pytest.raises(RuntimeError, match="old task failed"):
                    await old
            elif outcome in ("cancel", "cancel_waiter"):
                with pytest.raises(asyncio.CancelledError):
                    await old
            else:
                assert await old == 0

            # A detached task must neither evict nor start the replacement's TTL.
            assert cached.cache_contains("key")
            assert not replacement.done()
            call_later.assert_not_called()

            release[1].set()
            assert await replacement == 1
            assert call_later.call_count == 1
            assert await cached("key") == 1
            assert calls == 2
    finally:
        for event in release:
            event.set()
        tasks = [old] if replacement is None else [old, replacement]
        await asyncio.gather(*tasks, return_exceptions=True)
        await cached.cache_close()
        cached.cache_clear()
