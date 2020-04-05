import asyncio
from functools import partial

import pytest

from async_lru import alru_cache

alru_cache_attrs = [
    'hits',
    'misses',
    'tasks',
    'closed',
    'cache_info',
    'cache_clear',
    'invalidate',
    'close',
    'open',
]

alru_cache_calable_attrs = alru_cache_attrs.copy()
for attr in ['hits', 'misses', 'tasks', 'closed']:
    alru_cache_calable_attrs.remove(attr)


def test_alru_cache_not_callable(loop):
    with pytest.raises(NotImplementedError):
        alru_cache('foo')


def test_alru_cache_not_coroutine(loop):
    with pytest.raises(RuntimeError):
        @alru_cache
        def not_coro(val):
            return val


def test_alru_cache_deco(loop, check_lru):
    asyncio.set_event_loop(loop)

    @alru_cache
    async def coro():
        pass

    assert asyncio.iscoroutinefunction(coro)

    for attr in alru_cache_attrs:
        assert hasattr(coro, attr)
    for attr in alru_cache_calable_attrs:
        assert callable(getattr(coro, attr))

    assert isinstance(coro._cache, dict)
    assert isinstance(coro.tasks, set)
    check_lru(coro, hits=0, misses=0, cache=0, tasks=0)

    assert asyncio.iscoroutine(coro())


def test_alru_cache_deco_called(check_lru, loop):
    asyncio.set_event_loop(loop)

    @alru_cache()
    async def coro():
        pass

    assert asyncio.iscoroutinefunction(coro)

    for attr in alru_cache_attrs:
        assert hasattr(coro, attr)
    for attr in alru_cache_calable_attrs:
        assert callable(getattr(coro, attr))

    assert isinstance(coro._cache, dict)
    assert isinstance(coro.tasks, set)
    check_lru(coro, hits=0, misses=0, cache=0, tasks=0)

    assert asyncio.iscoroutine(coro())


def test_alru_cache_fn_called(check_lru, loop):
    asyncio.set_event_loop(loop)

    async def coro():
        pass

    coro_wrapped = alru_cache(coro)

    assert asyncio.iscoroutinefunction(coro_wrapped)

    for attr in alru_cache_attrs:
        assert hasattr(coro_wrapped, attr)
    for attr in alru_cache_calable_attrs:
        assert callable(getattr(coro_wrapped, attr))

    assert isinstance(coro_wrapped._cache, dict)
    assert isinstance(coro_wrapped.tasks, set)
    check_lru(coro_wrapped, hits=0, misses=0, cache=0, tasks=0)

    assert asyncio.iscoroutine(coro_wrapped())


def test_alru_cache_origin(loop):
    asyncio.set_event_loop(loop)

    async def coro():
        pass

    coro_wrapped = alru_cache(coro)

    assert coro_wrapped._origin is coro

    coro_wrapped = alru_cache(partial(coro))

    assert coro_wrapped._origin is coro


@pytest.mark.asyncio
async def test_alru_cache_await_same_result_async(check_lru, loop):
    calls = 0
    val = object()

    @alru_cache(loop=loop)
    async def coro():
        nonlocal calls
        calls += 1

        return val

    coros = [coro() for _ in range(100)]
    ret = await asyncio.gather(*coros, loop=loop)
    expected = [val] * 100
    assert ret == expected
    check_lru(coro, hits=99, misses=1, cache=1, tasks=0)

    assert calls == 1
    assert await coro() is val
    check_lru(coro, hits=100, misses=1, cache=1, tasks=0)


@pytest.mark.asyncio
async def test_alru_cache_await_same_result_coroutine(check_lru, loop):
    calls = 0
    val = object()

    @alru_cache(loop=loop)
    async def coro():
        nonlocal calls
        calls += 1

        return val

    coros = [coro() for _ in range(100)]
    ret = await asyncio.gather(*coros, loop=loop)
    expected = [val] * 100
    assert ret == expected
    check_lru(coro, hits=99, misses=1, cache=1, tasks=0)

    assert calls == 1
    assert await coro() is val
    check_lru(coro, hits=100, misses=1, cache=1, tasks=0)


@pytest.mark.asyncio
async def test_alru_cache_dict_not_shared(check_lru, loop):
    async def coro(val):
        return val

    coro1 = alru_cache(loop=loop)(coro)
    coro2 = alru_cache(loop=loop)(coro)

    ret1 = await coro1(1)
    check_lru(coro1, hits=0, misses=1, cache=1, tasks=0)

    ret2 = await coro2(1)
    check_lru(coro2, hits=0, misses=1, cache=1, tasks=0)

    assert ret1 == ret2

    assert coro1._cache[1].result() == coro2._cache[1].result()
    assert coro1._cache != coro2._cache
    assert coro1._cache.keys() == coro2._cache.keys()
    assert coro1._cache is not coro2._cache
