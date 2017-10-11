import asyncio
import gc
import os

import pytest

from async_lru import _CacheInfo

asyncio.set_event_loop(None)


@pytest.fixture
def event_loop(request):
    loop = asyncio.new_event_loop()
    loop.set_debug(bool(os.environ.get('PYTHONASYNCIODEBUG')))

    yield loop

    loop.call_soon(loop.stop)
    loop.run_forever()
    loop.close()

    gc.collect()


@pytest.fixture
def loop(event_loop, request):
    asyncio.set_event_loop(None)
    request.addfinalizer(lambda: asyncio.set_event_loop(None))

    return event_loop


@pytest.fixture
def check_lru(request):
    def _check_lru(wrapped, *, hits, misses, cache, tasks, maxsize=128):
        assert wrapped.hits == hits
        assert wrapped.misses == misses
        assert len(wrapped._cache) == cache
        assert len(wrapped.tasks) == tasks
        assert wrapped.cache_info() == _CacheInfo(
            hits=hits,
            misses=misses,
            maxsize=maxsize,
            currsize=cache,
        )

    return _check_lru
