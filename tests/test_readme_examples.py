import asyncio
import threading
from typing import Any

from async_lru import alru_cache


def test_readme_example_per_thread_caching() -> None:
    """Test per-thread caching pattern from README to avoid thread-safety issues."""
    _local = threading.local()

    def get_cached_fetcher() -> Any:
        if not hasattr(_local, "fetcher"):

            @alru_cache(maxsize=100)
            async def fetch_data(key: str) -> str:
                return f"data_{key}"

            _local.fetcher = fetch_data
        return _local.fetcher

    async def worker() -> tuple[str, Any]:
        fetcher = get_cached_fetcher()
        # Call again to ensure the pattern handles the "already exists" case
        fetcher_retry = get_cached_fetcher()
        assert fetcher is fetcher_retry

        result = await fetcher("some_key")
        return result, fetcher.cache_info()

    def thread_worker(results: list[tuple[str, Any]]) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(worker())
            results.append(result)
        finally:
            loop.close()

    results: list[tuple[str, Any]] = []
    threads = [
        threading.Thread(target=thread_worker, args=(results,)) for _ in range(3)
    ]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 3
    for result, cache_info in results:
        assert result == "data_some_key"
        assert cache_info.misses == 1
