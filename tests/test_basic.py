import asyncio
from functools import _CacheInfo, partial
from typing import Callable

import pytest

from async_lru import _CacheParameters, alru_cache


def test_alru_cache_not_callable() -> None:
    with pytest.raises(NotImplementedError):
        alru_cache("foo")  # type: ignore[call-overload]


def test_alru_cache_not_coroutine() -> None:
    with pytest.raises(RuntimeError):

        @alru_cache  # type: ignore[arg-type]
        def not_coro(val: int) -> int:
            return val


async def test_alru_cache_deco(check_lru: Callable[..., None]) -> None:
    @alru_cache
    async def coro() -> None:
        pass

    assert asyncio.iscoroutinefunction(coro)

    check_lru(coro, hits=0, misses=0, cache=0, tasks=0)

    awaitable = coro()
    assert asyncio.iscoroutine(awaitable)
    await awaitable


async def test_alru_cache_deco_called(check_lru: Callable[..., None]) -> None:
    @alru_cache()
    async def coro() -> None:
        pass

    assert asyncio.iscoroutinefunction(coro)

    check_lru(coro, hits=0, misses=0, cache=0, tasks=0)

    awaitable = coro()
    assert asyncio.iscoroutine(awaitable)
    await awaitable


async def test_alru_cache_fn_called(check_lru: Callable[..., None]) -> None:
    async def coro() -> None:
        pass

    coro_wrapped = alru_cache(coro)

    assert asyncio.iscoroutinefunction(coro_wrapped)

    check_lru(coro_wrapped, hits=0, misses=0, cache=0, tasks=0)

    awaitable = coro_wrapped()
    assert asyncio.iscoroutine(awaitable)
    await awaitable


async def test_alru_cache_partial() -> None:
    async def coro(val: int) -> int:
        return val

    coro_wrapped1 = alru_cache(coro)

    assert await coro_wrapped1(1) == 1

    coro_wrapped2 = alru_cache(partial(coro, 2))

    assert await coro_wrapped2() == 2


async def test_alru_cache_await_same_result_async(
    check_lru: Callable[..., None]
) -> None:
    calls = 0
    val = object()

    @alru_cache()
    async def coro() -> object:
        nonlocal calls
        calls += 1

        return val

    coros = [coro() for _ in range(100)]
    ret = await asyncio.gather(*coros)
    expected = [val] * 100
    assert ret == expected
    check_lru(coro, hits=99, misses=1, cache=1, tasks=0)

    assert calls == 1
    assert await coro() is val
    check_lru(coro, hits=100, misses=1, cache=1, tasks=0)


async def test_alru_cache_await_same_result_coroutine(
    check_lru: Callable[..., None]
) -> None:
    calls = 0
    val = object()

    @alru_cache()
    async def coro() -> object:
        nonlocal calls
        calls += 1

        return val

    coros = [coro() for _ in range(100)]
    ret = await asyncio.gather(*coros)
    expected = [val] * 100
    assert ret == expected
    check_lru(coro, hits=99, misses=1, cache=1, tasks=0)

    assert calls == 1
    assert await coro() is val
    check_lru(coro, hits=100, misses=1, cache=1, tasks=0)


async def test_alru_cache_dict_not_shared(check_lru: Callable[..., None]) -> None:
    async def coro(val: int) -> int:
        return val

    coro1 = alru_cache()(coro)
    coro2 = alru_cache()(coro)

    ret1 = await coro1(1)
    check_lru(coro1, hits=0, misses=1, cache=1, tasks=0)

    ret2 = await coro2(1)
    check_lru(coro2, hits=0, misses=1, cache=1, tasks=0)

    assert ret1 == ret2

    assert (
        coro1._LRUCacheWrapper__cache[1].fut.result()  # type: ignore[attr-defined]
        == coro2._LRUCacheWrapper__cache[1].fut.result()  # type: ignore[attr-defined]
    )
    assert coro1._LRUCacheWrapper__cache != coro2._LRUCacheWrapper__cache  # type: ignore[attr-defined]
    assert coro1._LRUCacheWrapper__cache.keys() == coro2._LRUCacheWrapper__cache.keys()  # type: ignore[attr-defined]
    assert coro1._LRUCacheWrapper__cache is not coro2._LRUCacheWrapper__cache  # type: ignore[attr-defined]


async def test_alru_cache_parameters() -> None:
    @alru_cache
    async def coro(val: int) -> int:
        return val

    assert coro.cache_parameters() == _CacheParameters(
        typed=False,
        maxsize=128,
        tasks=0,
        closed=False,
    )

    await coro(1)
    assert coro.cache_parameters() == _CacheParameters(
        typed=False,
        maxsize=128,
        tasks=0,
        closed=False,
    )


async def test_alru_cache_method() -> None:
    class A:
        def __init__(self, val: int) -> None:
            self.val = val

        @alru_cache
        async def coro(self) -> int:
            return self.val

    a = A(42)
    assert await a.coro() == 42
    assert a.coro.cache_parameters() == _CacheParameters(
        typed=False,
        maxsize=128,
        tasks=0,
        closed=False,
    )


async def test_invalidate_cache_for_method() -> None:
    class A:
        @alru_cache
        async def coro(self, val: int) -> int:
            return val

    a = A()
    assert await a.coro(42) == 42

    assert a.coro.cache_info() == _CacheInfo(0, 1, 128, 1)

    a.coro.cache_invalidate(42)

    assert a.coro.cache_info() == _CacheInfo(0, 1, 128, 0)
