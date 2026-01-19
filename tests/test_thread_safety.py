import asyncio
import threading

from async_lru import alru_cache


def test_cross_thread_access_raises_error() -> None:
    @alru_cache(maxsize=100, check_thread=True)
    async def cached_func(key: str) -> str:
        return f"data_{key}"

    async def use_cache() -> str:
        return await cached_func("test")

    loop1 = asyncio.new_event_loop()
    loop1.run_until_complete(use_cache())
    loop1.close()

    error_raised = threading.Event()
    error_message: list[str] = []

    def thread_worker() -> None:
        loop2 = asyncio.new_event_loop()
        asyncio.set_event_loop(loop2)
        try:
            loop2.run_until_complete(use_cache())
        except RuntimeError as e:
            error_message.append(str(e))
            error_raised.set()
        finally:
            loop2.close()

    thread = threading.Thread(target=thread_worker)
    thread.start()
    thread.join()

    assert (
        error_raised.is_set()
    ), "RuntimeError should be raised for cross-thread access"
    assert "not thread-safe" in error_message[0]


def test_same_thread_access_works() -> None:
    @alru_cache(maxsize=100)
    async def cached_func(key: str) -> str:
        return f"data_{key}"

    async def use_cache_multiple_times() -> list[str]:
        results = []
        results.append(await cached_func("a"))
        results.append(await cached_func("b"))
        results.append(await cached_func("a"))
        return results

    loop = asyncio.new_event_loop()
    try:
        results = loop.run_until_complete(use_cache_multiple_times())
    finally:
        loop.close()

    assert results == ["data_a", "data_b", "data_a"]


def test_cross_thread_cache_invalidate_raises_error() -> None:
    @alru_cache(maxsize=100, check_thread=True)
    async def cached_func(key: str) -> str:
        return f"data_{key}"

    async def use_cache() -> str:
        return await cached_func("test")

    loop = asyncio.new_event_loop()
    loop.run_until_complete(use_cache())
    loop.close()

    error_raised = threading.Event()
    error_message: list[str] = []

    def thread_worker() -> None:
        try:
            cached_func.cache_invalidate("test")
        except RuntimeError as e:
            error_message.append(str(e))
            error_raised.set()

    thread = threading.Thread(target=thread_worker)
    thread.start()
    thread.join()

    assert (
        error_raised.is_set()
    ), "RuntimeError should be raised for cross-thread cache_invalidate"
    assert "not thread-safe" in error_message[0]


def test_cross_thread_cache_clear_raises_error() -> None:
    @alru_cache(maxsize=100, check_thread=True)
    async def cached_func(key: str) -> str:
        return f"data_{key}"

    async def use_cache() -> str:
        return await cached_func("test")

    loop = asyncio.new_event_loop()
    loop.run_until_complete(use_cache())
    loop.close()

    error_raised = threading.Event()
    error_message: list[str] = []

    def thread_worker() -> None:
        try:
            cached_func.cache_clear()
        except RuntimeError as e:
            error_message.append(str(e))
            error_raised.set()

    thread = threading.Thread(target=thread_worker)
    thread.start()
    thread.join()

    assert (
        error_raised.is_set()
    ), "RuntimeError should be raised for cross-thread cache_clear"
    assert "not thread-safe" in error_message[0]


def test_cross_thread_cache_close_raises_error() -> None:
    @alru_cache(maxsize=100, check_thread=True)
    async def cached_func(key: str) -> str:
        return f"data_{key}"

    async def use_cache() -> str:
        return await cached_func("test")

    loop = asyncio.new_event_loop()
    loop.run_until_complete(use_cache())
    loop.close()

    error_raised = threading.Event()
    error_message: list[str] = []

    def thread_worker() -> None:
        loop2 = asyncio.new_event_loop()
        asyncio.set_event_loop(loop2)
        try:
            loop2.run_until_complete(cached_func.cache_close())
        except RuntimeError as e:
            error_message.append(str(e))
            error_raised.set()
        finally:
            loop2.close()

    thread = threading.Thread(target=thread_worker)
    thread.start()
    thread.join()

    assert (
        error_raised.is_set()
    ), "RuntimeError should be raised for cross-thread cache_close"
    assert "not thread-safe" in error_message[0]
