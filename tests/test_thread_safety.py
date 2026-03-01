import asyncio
import warnings

import pytest

from async_lru import AlruCacheLoopResetWarning, alru_cache


@pytest.mark.filterwarnings("ignore::async_lru.AlruCacheLoopResetWarning")
def test_cross_loop_auto_resets_cache() -> None:
    @alru_cache(maxsize=100)
    async def cached_func(key: str) -> str:
        return f"data_{key}"

    loop1 = asyncio.new_event_loop()
    loop1.run_until_complete(cached_func("test"))
    loop1.close()

    assert cached_func.cache_info().currsize == 1

    loop2 = asyncio.new_event_loop()
    result = loop2.run_until_complete(cached_func("test"))
    loop2.close()

    assert result == "data_test"
    # Cache was cleared on loop change, so the old entry is gone.
    # The new call re-populated it as a miss.
    assert cached_func.cache_info().hits == 0
    assert cached_func.cache_info().misses == 1


@pytest.mark.filterwarnings("ignore::async_lru.AlruCacheLoopResetWarning")
def test_cross_loop_preserves_stats_reset() -> None:
    @alru_cache(maxsize=100)
    async def cached_func(key: str) -> str:
        return f"data_{key}"

    loop1 = asyncio.new_event_loop()
    loop1.run_until_complete(cached_func("a"))
    loop1.run_until_complete(cached_func("a"))
    loop1.close()

    assert cached_func.cache_info().hits == 1
    assert cached_func.cache_info().misses == 1

    loop2 = asyncio.new_event_loop()
    loop2.run_until_complete(cached_func("a"))
    loop2.close()

    # Stats were reset on loop change (cache_clear resets hits/misses)
    assert cached_func.cache_info().hits == 0
    assert cached_func.cache_info().misses == 1


@pytest.mark.filterwarnings("ignore::async_lru.AlruCacheLoopResetWarning")
def test_invalid_key_does_not_bind_loop() -> None:
    @alru_cache(maxsize=100)
    async def cached_func(key: object) -> str:
        return f"data_{key}"

    loop1 = asyncio.new_event_loop()
    error_raised = False
    try:
        loop1.run_until_complete(cached_func([]))
    except TypeError:
        error_raised = True
    finally:
        loop1.close()

    assert error_raised, "TypeError should be raised for unhashable key"

    loop2 = asyncio.new_event_loop()
    try:
        result = loop2.run_until_complete(cached_func("ok"))
    finally:
        loop2.close()

    assert result == "data_ok"


def test_same_loop_access_works() -> None:
    @alru_cache(maxsize=100)
    async def cached_func(key: str) -> str:
        return f"data_{key}"

    async def run_test() -> list[str]:
        results = []
        results.append(await cached_func("a"))
        results.append(await cached_func("b"))
        results.append(await cached_func("a"))
        return results

    loop = asyncio.new_event_loop()
    results = loop.run_until_complete(run_test())
    loop.close()

    assert results == ["data_a", "data_b", "data_a"]
    assert cached_func.cache_info().hits == 1


def test_cross_loop_cache_close_works() -> None:
    @alru_cache(maxsize=100)
    async def cached_func(key: str) -> str:
        return f"data_{key}"

    loop1 = asyncio.new_event_loop()
    loop1.run_until_complete(cached_func("test"))
    loop1.close()

    loop2 = asyncio.new_event_loop()
    loop2.run_until_complete(cached_func.cache_close())
    loop2.close()


def test_sync_methods_work_without_loop_check() -> None:
    @alru_cache(maxsize=100)
    async def cached_func(key: str) -> str:
        return f"data_{key}"

    loop1 = asyncio.new_event_loop()
    loop1.run_until_complete(cached_func("test"))
    loop1.close()

    cached_func.cache_invalidate("test")
    assert cached_func.cache_info().currsize == 0

    cached_func.cache_clear()
    assert cached_func.cache_info().currsize == 0


def test_concurrent_same_loop_works() -> None:
    @alru_cache(maxsize=100)
    async def cached_func(key: str) -> str:
        await asyncio.sleep(0.01)
        return f"data_{key}"

    async def run_concurrent() -> list[str]:
        tasks = [cached_func("test") for _ in range(3)]
        return await asyncio.gather(*tasks)

    loop = asyncio.new_event_loop()
    results = loop.run_until_complete(run_concurrent())
    loop.close()

    assert results == ["data_test"] * 3
    assert cached_func.cache_info().hits == 2


@pytest.mark.filterwarnings("ignore::async_lru.AlruCacheLoopResetWarning")
def test_multiple_loop_transitions() -> None:
    @alru_cache(maxsize=100)
    async def cached_func(key: str) -> str:
        return f"data_{key}"

    for i in range(5):
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(cached_func("test"))
        loop.close()
        assert result == "data_test"


def test_loop_change_emits_warning() -> None:
    @alru_cache(maxsize=100)
    async def cached_func(key: str) -> str:
        return f"data_{key}"

    loop1 = asyncio.new_event_loop()
    loop1.run_until_complete(cached_func("test"))
    loop1.close()

    loop2 = asyncio.new_event_loop()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        loop2.run_until_complete(cached_func("test"))
    loop2.close()

    assert len(w) == 1
    assert issubclass(w[0].category, AlruCacheLoopResetWarning)
    assert "event loop change" in str(w[0].message)


def test_loop_change_warns_only_once() -> None:
    @alru_cache(maxsize=100)
    async def cached_func(key: str) -> str:
        return f"data_{key}"

    all_warnings: list[warnings.WarningMessage] = []
    for _ in range(4):
        loop = asyncio.new_event_loop()
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            loop.run_until_complete(cached_func("test"))
        loop.close()
        all_warnings.extend(w)

    reset_warnings = [
        w for w in all_warnings if issubclass(w.category, AlruCacheLoopResetWarning)
    ]
    assert len(reset_warnings) == 1
