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


def test_alru_cache_deco(loop):
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
    assert len(coro._cache) == 0
    assert len(coro.tasks) == 0
    assert not coro.closed
    assert coro.cache_info() == (0, 0, 128, 0)
    assert isinstance(coro._cache, dict)
    assert coro.hits == coro.misses == 0

    assert asyncio.iscoroutine(coro())


def test_alru_cache_deco_called(loop):
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
    assert len(coro._cache) == 0
    assert len(coro.tasks) == 0
    assert not coro.closed
    assert coro.cache_info() == (0, 0, 128, 0)
    assert isinstance(coro._cache, dict)
    assert coro.hits == coro.misses == 0

    assert asyncio.iscoroutine(coro())


def test_alru_cache_fn_called(loop):
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
    assert len(coro_wrapped._cache) == 0
    assert len(coro_wrapped.tasks) == 0
    assert not coro_wrapped.closed
    assert coro_wrapped.cache_info() == (0, 0, 128, 0)
    assert coro_wrapped.hits == coro_wrapped.misses == 0

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
async def test_alru_cache_close(loop):
    asyncio.set_event_loop(loop)

    @alru_cache
    async def coro():
        pass

    assert not coro.closed

    await coro()

    coro.close()

    assert coro.closed

    with pytest.raises(RuntimeError):
        await coro()

    with pytest.raises(RuntimeError):
        coro.close()


def test_alru_cache_open(loop):
    asyncio.set_event_loop(loop)

    @alru_cache
    async def coro():
        pass

    coro.close()

    coro.open()

    assert not coro.closed

    with pytest.raises(RuntimeError):
        coro.open()
