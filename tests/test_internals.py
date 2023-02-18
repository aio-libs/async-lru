import asyncio
from functools import _make_key, partial
from typing import Tuple
from unittest import mock

import pytest

from async_lru import _done_callback, _LRUCacheWrapper


async def test_done_callback_cancelled() -> None:
    loop = asyncio.get_running_loop()
    task = loop.create_future()
    fut = loop.create_future()

    task.add_done_callback(partial(_done_callback, fut))

    task.cancel()

    await asyncio.sleep(0)

    assert fut.cancelled()


async def test_done_callback_exception() -> None:
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


async def test_done_callback() -> None:
    loop = asyncio.get_running_loop()
    task = loop.create_future()
    fut = loop.create_future()

    task.add_done_callback(partial(_done_callback, fut))

    task.set_result(1)

    await asyncio.sleep(0)

    assert fut.result() == 1


def test_cache_invalidate_typed() -> None:
    wrapped = _LRUCacheWrapper(mock.ANY, None, True, True)

    args: Tuple[int | float] = (1,)
    kwargs = {"1": 1}

    from_cache = wrapped.invalidate(*args, **kwargs)

    assert not from_cache

    key = _make_key(args, kwargs, True)

    wrapped._LRUCacheWrapper__cache[key] = 0  # type: ignore[attr-defined]

    from_cache = wrapped.invalidate(*args, **kwargs)

    assert from_cache

    assert len(wrapped._LRUCacheWrapper__cache) == 0  # type: ignore[attr-defined]

    wrapped._LRUCacheWrapper__cache[key] = 0  # type: ignore[attr-defined]

    args = (1.0,)

    from_cache = wrapped.invalidate(*args, **kwargs)

    assert not from_cache

    wrapped._LRUCacheWrapper__cache[key] = 1  # type: ignore[attr-defined]


def test_cache_invalidate_not_typed() -> None:
    wrapped = _LRUCacheWrapper(mock.ANY, None, False, True)

    args: Tuple[int | float] = (1,)
    kwargs = {"1": 1}

    from_cache = wrapped.invalidate(*args, **kwargs)

    assert not from_cache

    key = _make_key(args, kwargs, False)

    wrapped._LRUCacheWrapper__cache[key] = 0  # type: ignore[attr-defined]

    from_cache = wrapped.invalidate(*args, **kwargs)

    assert from_cache

    assert len(wrapped._LRUCacheWrapper__cache) == 0  # type: ignore[attr-defined]

    wrapped._LRUCacheWrapper__cache[key] = 0  # type: ignore[attr-defined]

    args = (1.0,)

    from_cache = wrapped.invalidate(*args, **kwargs)

    assert from_cache

    assert len(wrapped._LRUCacheWrapper__cache) == 0  # type: ignore[attr-defined]


async def test_cache_clear() -> None:
    wrapped = _LRUCacheWrapper(mock.AsyncMock(return_value=1), None, True, True)

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


def test_open() -> None:
    wrapped = _LRUCacheWrapper(mock.ANY, None, True, True)
    wrapped._LRUCacheWrapper__hits = 1  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__misses = 1  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__cache = {}  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__tasks = set()  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__closed = True  # type: ignore[attr-defined]

    with pytest.raises(RuntimeError):
        wrapped.open()

    wrapped._LRUCacheWrapper__hits = 0  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__misses = 0  # type: ignore[attr-defined]

    wrapped.open()

    assert not wrapped.closed

    with pytest.raises(RuntimeError):
        wrapped.open()


async def test_close() -> None:
    loop = asyncio.get_running_loop()
    wrapped = _LRUCacheWrapper(mock.ANY, None, True, True)

    awaitable = wrapped.close(cancel=False, return_exceptions=True)
    await awaitable

    assert wrapped.closed

    with pytest.raises(RuntimeError):
        wrapped.close(cancel=False, return_exceptions=True)

    fut = loop.create_future()
    wrapped._LRUCacheWrapper__closed = False  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__tasks = {fut}  # type: ignore[attr-defined]

    awaitable = wrapped.close(cancel=True, return_exceptions=True)
    await awaitable

    assert fut.cancelled()

    fut = loop.create_future()
    fut.set_result(None)
    wrapped._LRUCacheWrapper__closed = False  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__tasks = {fut}  # type: ignore[attr-defined]

    awaitable = wrapped.close(cancel=True, return_exceptions=True)
    await awaitable

    assert not fut.cancelled()

    fut = loop.create_future()
    fut.set_exception(ZeroDivisionError)
    wrapped._LRUCacheWrapper__closed = False  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__tasks = {fut}  # type: ignore[attr-defined]

    awaitable = wrapped.close(cancel=True, return_exceptions=True)
    await awaitable

    assert not fut.cancelled()


async def test_wait_closed() -> None:
    loop = asyncio.get_running_loop()
    wrapped = _LRUCacheWrapper(mock.ANY, None, True, True)

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
    wrapped._LRUCacheWrapper__tasks = {fut}  # type: ignore[attr-defined]
    with mock.patch.object(_LRUCacheWrapper, "_close_waited") as mocked:
        ret = await wrapped._wait_closed(
            return_exceptions=True,
        )
        assert ret == [None]
        assert mocked.called_once()

    exc = ZeroDivisionError()
    fut = loop.create_future()
    fut.set_exception(exc)
    wrapped._LRUCacheWrapper__tasks = {fut}  # type: ignore[attr-defined]
    with mock.patch.object(_LRUCacheWrapper, "_close_waited") as mocked:
        ret = await wrapped._wait_closed(
            return_exceptions=True,
        )
        assert ret == [exc]
        assert mocked.called_once()

    fut = loop.create_future()
    fut.set_exception(ZeroDivisionError)
    wrapped._LRUCacheWrapper__tasks = {fut}  # type: ignore[attr-defined]
    with mock.patch.object(_LRUCacheWrapper, "_close_waited") as mocked:
        with pytest.raises(ZeroDivisionError):
            await wrapped._wait_closed(
                return_exceptions=False,
            )
        assert mocked.called_once()


def test_close_waited() -> None:
    wrapped = _LRUCacheWrapper(mock.ANY, None, True, True)

    with mock.patch.object(_LRUCacheWrapper, "cache_clear") as mocked:
        wrapped._close_waited(mock.ANY)

        assert mocked.called_once()


def test_cache_info() -> None:
    wrapped = _LRUCacheWrapper(mock.ANY, 3, True, True)

    assert (0, 0, 3, 0) == wrapped.cache_info()

    wrapped._LRUCacheWrapper__cache[1] = 1  # type: ignore[attr-defined]

    assert (0, 0, 3, 1) == wrapped.cache_info()

    wrapped._LRUCacheWrapper__hits = 2  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__misses = 3  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__cache[2] = 2  # type: ignore[attr-defined]

    assert (2, 3, 3, 2) == wrapped.cache_info()


def test__cache_touch() -> None:
    wrapped = _LRUCacheWrapper(mock.ANY, None, True, True)

    wrapped._LRUCacheWrapper__cache[1] = 1  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__cache[2] = 2  # type: ignore[attr-defined]

    wrapped._LRUCacheWrapper__cache_touch(1)  # type: ignore[attr-defined]
    assert list(wrapped._LRUCacheWrapper__cache) == [2, 1]  # type: ignore[attr-defined]

    wrapped._LRUCacheWrapper__cache_touch(2)  # type: ignore[attr-defined]
    assert list(wrapped._LRUCacheWrapper__cache) == [1, 2]  # type: ignore[attr-defined]

    # test KeyError
    wrapped._LRUCacheWrapper__cache_touch(100)  # type: ignore[attr-defined]


def test_cache_hit() -> None:
    wrapped = _LRUCacheWrapper(mock.ANY, None, True, True)
    wrapped._LRUCacheWrapper__hits = 1  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__cache[1] = 1  # type: ignore[attr-defined]

    with mock.patch.object(_LRUCacheWrapper, "_LRUCacheWrapper__cache_touch") as mocked:
        wrapped._cache_hit(1)

        assert mocked.called_once()

    assert wrapped.hits == 2

    wrapped._cache_hit(1)

    assert wrapped.hits == 3


def test_cache_miss() -> None:
    wrapped = _LRUCacheWrapper(mock.ANY, None, True, True)
    wrapped._LRUCacheWrapper__misses = 1  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__cache[1] = 1  # type: ignore[attr-defined]

    with mock.patch.object(_LRUCacheWrapper, "_LRUCacheWrapper__cache_touch") as mocked:
        wrapped._cache_miss(1)

        assert mocked.called_once()

    assert wrapped.misses == 2

    wrapped._cache_miss(1)

    assert wrapped.misses == 3
