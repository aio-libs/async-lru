import asyncio

from async_lru import alru_cache


def test_cross_loop_access_raises_error() -> None:
    @alru_cache(maxsize=100)
    async def cached_func(key: str) -> str:
        return f"data_{key}"

    loop1 = asyncio.new_event_loop()
    loop1.run_until_complete(cached_func("test"))
    loop1.close()

    loop2 = asyncio.new_event_loop()
    error_raised = False
    error_message = ""
    try:
        loop2.run_until_complete(cached_func("test"))
    except RuntimeError as e:
        error_raised = True
        error_message = str(e)
    finally:
        loop2.close()

    assert error_raised, "RuntimeError should be raised for cross-loop access"
    assert "event loop" in error_message.lower()


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


def test_cross_loop_cache_close_raises_error() -> None:
    @alru_cache(maxsize=100)
    async def cached_func(key: str) -> str:
        return f"data_{key}"

    loop1 = asyncio.new_event_loop()
    loop1.run_until_complete(cached_func("test"))
    loop1.close()

    loop2 = asyncio.new_event_loop()
    error_raised = False
    try:
        loop2.run_until_complete(cached_func.cache_close())
    except RuntimeError:
        error_raised = True
    finally:
        loop2.close()

    assert error_raised, "RuntimeError should be raised for cross-loop cache_close"


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
