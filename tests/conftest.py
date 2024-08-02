import sys
from functools import _CacheInfo
from typing import Callable, TypeVar

import pytest

from async_lru import _LRUCacheWrapper


if sys.version_info >= (3, 10):
    from typing import ParamSpec
else:
    from typing_extensions import ParamSpec


_T = TypeVar("_T")
_P = ParamSpec("_P")


@pytest.fixture
def check_lru() -> Callable[..., None]:  # type: ignore[misc]
    def _check_lru(
        wrapped: _LRUCacheWrapper[_P, _T],
        *,
        hits: int,
        misses: int,
        cache: int,
        tasks: int,
        maxsize: int = 128
    ) -> None:
        assert wrapped.cache_info() == _CacheInfo(
            hits=hits,
            misses=misses,
            maxsize=maxsize,
            currsize=cache,
        )
        assert wrapped.cache_parameters()["tasks"] == tasks

    return _check_lru
