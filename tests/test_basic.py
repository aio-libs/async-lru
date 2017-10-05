import pytest
from async_lru import alru_cache


def test_alru_cache_not_callable(loop):
    with pytest.raises(NotImplementedError):
        alru_cache('foo')


def test_alru_cache_not_coroutine(loop):
    with pytest.raises(RuntimeError):
        @alru_cache
        def not_coro(val):
            return val
