import pytest

from async_lru import _CacheInfo


@pytest.fixture
def check_lru(request):
    def _check_lru(wrapped, *, hits, misses, cache, tasks, maxsize=128):
        assert wrapped.hits == hits
        assert wrapped.misses == misses
        assert len(wrapped._LRUCacheWrapper__cache) == cache
        assert len(wrapped.tasks) == tasks
        assert wrapped.cache_info() == _CacheInfo(
            hits=hits,
            misses=misses,
            maxsize=maxsize,
            currsize=cache,
        )

    return _check_lru
