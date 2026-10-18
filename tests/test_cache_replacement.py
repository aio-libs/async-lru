import asyncio

import pytest

from async_lru import alru_cache


@pytest.mark.parametrize("fail_first", [True, False])
async def test_old_failure_does_not_remove_replacement(fail_first: bool) -> None:
    started = asyncio.Event()
    release = asyncio.Event()
    calls = 0

    @alru_cache()
    async def cached(key: str) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            started.set()
            await release.wait()
            raise RuntimeError("old request failed")
        return "fresh"

    old = asyncio.create_task(cached("key"))
    await started.wait()
    assert cached.cache_invalidate("key")
    assert await cached("key") == "fresh"

    if fail_first:
        release.set()
        with pytest.raises(RuntimeError, match="old request failed"):
            await old
    else:
        old.cancel()
        with pytest.raises(asyncio.CancelledError):
            await old
    await asyncio.sleep(0)

    try:
        assert cached.cache_contains("key")
        assert await cached("key") == "fresh"
        assert calls == 2
    finally:
        await cached.cache_close()


async def test_old_success_does_not_expire_pending_replacement() -> None:
    first_started = asyncio.Event()
    first_release = asyncio.Event()
    second_started = asyncio.Event()
    second_release = asyncio.Event()
    calls = 0

    @alru_cache(ttl=0.01)
    async def cached(key: str) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            first_started.set()
            await first_release.wait()
            return "old"
        second_started.set()
        await second_release.wait()
        return "fresh"

    old = asyncio.create_task(cached("key"))
    await first_started.wait()
    assert cached.cache_invalidate("key")
    replacement = asyncio.create_task(cached("key"))
    await second_started.wait()
    first_release.set()
    assert await old == "old"
    await asyncio.sleep(0.02)

    try:
        assert cached.cache_contains("key")
    finally:
        second_release.set()
        assert await replacement == "fresh"
        await cached.cache_close()
