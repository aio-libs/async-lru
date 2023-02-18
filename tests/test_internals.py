import asyncio
from collections import OrderedDict
from functools import _make_key, partial
from unittest import mock

import pytest

from async_lru import _done_callback, _LRUCacheWrapper


async def test_done_callback_cancelled():
    loop = asyncio.get_running_loop()
    task = loop.create_future()
    fut = loop.create_future()

    task.add_done_callback(partial(_done_callback, fut))

    task.cancel()

    await asyncio.sleep(0)

    assert fut.cancelled()


async def test_done_callback_exception():
    loop = asyncio.get_running_loop()
    task = loop.create_future()
    fut = loop.create_future()

    task.add_done_callback(partial(_done_callback, fut))

    exc = ZeroDivisionError()

    task.set_exception(exc)

    await asyncio.sleep(0)

    with pytest.raises(ZeroDivisionError):
        await fut

    with pytest.raises(ZeroDivisionError):
        fut.result()

    assert fut.exception() is exc


async def test_done_callback():
    loop = asyncio.get_running_loop()
    task = loop.create_future()
    fut = loop.create_future()

    task.add_done_callback(partial(_done_callback, fut))

    task.set_result(1)

    await asyncio.sleep(0)

    assert fut.result() == 1


def test_cache_invalidate_typed():
    wrapped = _LRUCacheWrapper(mock.ANY, mock.ANY, None, True, True)

    args = (1,)
    kwargs = {"1": 1}

    from_cache = wrapped.invalidate(*args, **kwargs)

    assert not from_cache

    key = _make_key(args, kwargs, True)

    wrapped._LRUCacheWrapper__cache[key] = 0

    from_cache = wrapped.invalidate(*args, **kwargs)

    assert from_cache

    assert len(wrapped._LRUCacheWrapper__cache) == 0

    wrapped._LRUCacheWrapper__cache[key] = 0

    args = (1.0,)

    from_cache = wrapped.invalidate(*args, **kwargs)

    assert not from_cache

    wrapped._LRUCacheWrapper__cache[key] = 1


def test_cache_invalidate_not_typed():
    wrapped = _LRUCacheWrapper(mock.ANY, mock.ANY, None, False, True)

    args = (1,)
    kwargs = {"1": 1}

    from_cache = wrapped.invalidate(*args, **kwargs)

    assert not from_cache

    key = _make_key(args, kwargs, False)

    wrapped._LRUCacheWrapper__cache[key] = 0

    from_cache = wrapped.invalidate(*args, **kwargs)

    assert from_cache

    assert len(wrapped._LRUCacheWrapper__cache) == 0

    wrapped._LRUCacheWrapper__cache[key] = 0

    args = (1.0,)

    from_cache = wrapped.invalidate(*args, **kwargs)

    assert from_cache

    assert len(wrapped._LRUCacheWrapper__cache) == 0


async def test_cache_clear():
    wrapped = _LRUCacheWrapper(
        mock.AsyncMock(return_value=1), mock.ANY, None, True, True
    )

    await wrapped(123)

    assert wrapped.cache_info().hits == 0
    assert wrapped.cache_info().misses == 1
    assert wrapped.cache_info().currsize == 1
    assert len(wrapped.tasks) == 0

    await wrapped(123)
    assert wrapped.cache_info().hits == 1
    assert wrapped.cache_info().misses == 1
    assert wrapped.cache_info().currsize == 1
    assert len(wrapped.tasks) == 0

    wrapped.cache_clear()

    assert wrapped.cache_info().hits == 0
    assert wrapped.cache_info().misses == 0
    assert wrapped.cache_info().currsize == 0
    assert len(wrapped.tasks) == 0


def test_open():
    wrapped = _LRUCacheWrapper(mock.ANY, mock.ANY, None, True, True)
    wrapped._LRUCacheWrapper__hits = wrapped._LRUCacheWrapper__misses = 1
    wrapped._LRUCacheWrapper__cache = {}
    wrapped._LRUCacheWrapper__tasks = set()
    wrapped._LRUCacheWrapper__closed = True

    with pytest.raises(RuntimeError):
        wrapped.open()

    wrapped._LRUCacheWrapper__hits = wrapped._LRUCacheWrapper__misses = 0

    wrapped.open()

    assert not wrapped.closed

    with pytest.raises(RuntimeError):
        wrapped.open()


async def test_close():
    loop = asyncio.get_running_loop()
    wrapped = _LRUCacheWrapper(mock.ANY, mock.ANY, None, True, True)

    awaitable = wrapped.close(cancel=False, return_exceptions=True)
    await awaitable

    assert wrapped.closed

    with pytest.raises(RuntimeError):
        wrapped.close(cancel=False, return_exceptions=True)

    fut = loop.create_future()
    wrapped._LRUCacheWrapper__closed = False
    wrapped._LRUCacheWrapper__tasks = {fut}

    awaitable = wrapped.close(cancel=True, return_exceptions=True)
    await awaitable

    assert fut.cancelled()

    fut = loop.create_future()
    fut.set_result(None)
    wrapped._LRUCacheWrapper__closed = False
    wrapped._LRUCacheWrapper__tasks = {fut}

    awaitable = wrapped.close(cancel=True, return_exceptions=True)
    await awaitable

    assert not fut.cancelled()

    fut = loop.create_future()
    fut.set_exception(ZeroDivisionError)
    wrapped._LRUCacheWrapper__closed = False
    wrapped._LRUCacheWrapper__tasks = {fut}

    awaitable = wrapped.close(cancel=True, return_exceptions=True)
    await awaitable

    assert not fut.cancelled()


async def test_wait_closed():
    loop = asyncio.get_running_loop()
    wrapped = _LRUCacheWrapper(mock.ANY, mock.ANY, None, True, True)

    with mock.patch.object(_LRUCacheWrapper, "_close_waited") as mocked:
        ret = await wrapped._wait_closed(
            return_exceptions=True,
        )
        assert ret == []
        assert mocked.called_once()

    with mock.patch.object(_LRUCacheWrapper, "_close_waited") as mocked:
        ret = await wrapped._wait_closed(
            return_exceptions=True,
        )
        assert ret == []
        assert mocked.called_once()

    fut = loop.create_future()
    fut.set_result(None)
    wrapped._LRUCacheWrapper__tasks = {fut}
    with mock.patch.object(_LRUCacheWrapper, "_close_waited") as mocked:
        ret = await wrapped._wait_closed(
            return_exceptions=True,
        )
        assert ret == [None]
        assert mocked.called_once()

    exc = ZeroDivisionError()
    fut = loop.create_future()
    fut.set_exception(exc)
    wrapped._LRUCacheWrapper__tasks = {fut}
    with mock.patch.object(_LRUCacheWrapper, "_close_waited") as mocked:
        ret = await wrapped._wait_closed(
            return_exceptions=True,
        )
        assert ret == [exc]
        assert mocked.called_once()

    fut = loop.create_future()
    fut.set_exception(ZeroDivisionError)
    wrapped._LRUCacheWrapper__tasks = {fut}
    with mock.patch.object(_LRUCacheWrapper, "_close_waited") as mocked:
        with pytest.raises(ZeroDivisionError):
            await wrapped._wait_closed(
                return_exceptions=False,
            )
        assert mocked.called_once()


def test_close_waited():
    wrapped = _LRUCacheWrapper(mock.ANY, mock.ANY, None, True, True)

    with mock.patch.object(_LRUCacheWrapper, "cache_clear") as mocked:
        wrapped._close_waited(None)

        assert mocked.called_once()


def test_cache_info():
    wrapped = _LRUCacheWrapper(mock.ANY, mock.ANY, 3, True, True)

    assert (0, 0, 3, 0) == wrapped.cache_info()

    wrapped._LRUCacheWrapper__cache[1] = 1

    assert (0, 0, 3, 1) == wrapped.cache_info()

    wrapped._LRUCacheWrapper__hits = 2
    wrapped._LRUCacheWrapper__misses = 3
    wrapped._LRUCacheWrapper__cache[2] = 2

    assert (2, 3, 3, 2) == wrapped.cache_info()


def test__cache_touch():
    wrapped = _LRUCacheWrapper(mock.ANY, mock.ANY, None, True, True)

    wrapped._LRUCacheWrapper__cache[1] = 1
    wrapped._LRUCacheWrapper__cache[2] = 2

    wrapped._LRUCacheWrapper__cache_touch(1)
    assert list(wrapped._LRUCacheWrapper__cache) == [2, 1]

    wrapped._LRUCacheWrapper__cache_touch(2)
    assert list(wrapped._LRUCacheWrapper__cache) == [1, 2]

    # test KeyError
    wrapped._LRUCacheWrapper__cache_touch(100)


def test_cache_hit():
    wrapped = _LRUCacheWrapper(mock.ANY, mock.ANY, None, True, True)
    wrapped._LRUCacheWrapper__hits = 1
    wrapped._LRUCacheWrapper__cache[1] = 1

    with mock.patch.object(_LRUCacheWrapper, "_LRUCacheWrapper__cache_touch") as mocked:
        wrapped._cache_hit(1)

        assert mocked.called_once()

    assert wrapped.hits == 2

    wrapped._cache_hit(1)

    assert wrapped.hits == 3


def test_cache_miss():
    wrapped = _LRUCacheWrapper(mock.ANY, mock.ANY, None, True, True)
    wrapped._LRUCacheWrapper__misses = 1
    wrapped._LRUCacheWrapper__cache[1] = 1

    with mock.patch.object(_LRUCacheWrapper, "_LRUCacheWrapper__cache_touch") as mocked:
        wrapped._cache_miss(1)

        assert mocked.called_once()

    assert wrapped.misses == 2

    wrapped._cache_miss(1)

    assert wrapped.misses == 3
