from functools import _CacheInfo
from typing import Callable

import pytest

from async_lru import _R, _LRUCacheWrapper


@pytest.fixture
def check_lru() -> Callable[..., None]:
    def _check_lru(
        wrapped: _LRUCacheWrapper[_R],
        *,
        hits: int,
        misses: int,
        cache: int,
        tasks: int,
        maxsize: int = 128
    ) -> None:
        assert wrapped.hits == hits
        assert wrapped.misses == misses
        assert len(wrapped._LRUCacheWrapper__cache) == cache  # type: ignore[attr-defined]
        assert len(wrapped.tasks) == tasks
        assert wrapped.cache_info() == _CacheInfo(
            hits=hits,
            misses=misses,
            maxsize=maxsize,
            currsize=cache,
        )

    return _check_lru
