import asyncio
from functools import partial
from unittest import mock

import pytest

from async_lru import _LRUCacheWrapper


async def test_done_callback_cancelled() -> None:
    wrapped = _LRUCacheWrapper(mock.ANY, None, False, False, None)
    loop = asyncio.get_running_loop()
    task = loop.create_future()
    fut = loop.create_future()

    key = 1

    task.add_done_callback(partial(wrapped._task_done_callback, fut, key))
    wrapped._LRUCacheWrapper__tasks.add(task)  # type: ignore[attr-defined]

    task.cancel()

    await asyncio.sleep(0)

    assert fut.cancelled()


async def test_done_callback_exception() -> None:
    wrapped = _LRUCacheWrapper(mock.ANY, None, False, False, None)
    loop = asyncio.get_running_loop()
    task = loop.create_future()
    fut = loop.create_future()

    key = 1

    task.add_done_callback(partial(wrapped._task_done_callback, fut, key))
    wrapped._LRUCacheWrapper__tasks.add(task)  # type: ignore[attr-defined]

    exc = ZeroDivisionError()

    task.set_exception(exc)

    await asyncio.sleep(0)

    with pytest.raises(ZeroDivisionError):
        await fut

    with pytest.raises(ZeroDivisionError):
        fut.result()

    assert fut.exception() is exc


async def test_done_callback() -> None:
    wrapped = _LRUCacheWrapper(mock.ANY, None, False, False, None)
    loop = asyncio.get_running_loop()
    task = loop.create_future()

    key = 1
    fut = loop.create_future()

    task.add_done_callback(partial(wrapped._task_done_callback, fut, key))
    wrapped._LRUCacheWrapper__tasks.add(task)  # type: ignore[attr-defined]

    task.set_result(1)

    await asyncio.sleep(0)

    assert fut.result() == 1


async def test_cache_invalidate_typed() -> None:
    wrapped = _LRUCacheWrapper(mock.AsyncMock(return_value=1), None, True, True, None)

    from_cache = wrapped.cache_invalidate(1, a=1)

    assert not from_cache

    await wrapped(1, a=1)

    from_cache = wrapped.cache_invalidate(1, a=1)

    assert from_cache

    assert wrapped.cache_info().currsize == 0

    from_cache = wrapped.cache_invalidate(1.0, a=1)
    assert not from_cache

    assert wrapped.cache_info().currsize == 0
    await wrapped(1.0, a=1)
    assert wrapped.cache_info().currsize == 1
    from_cache = wrapped.cache_invalidate(1.0, a=1)
    assert from_cache


async def test_cache_invalidate_not_typed() -> None:
    wrapped = _LRUCacheWrapper(mock.AsyncMock(return_value=1), None, False, True, None)

    from_cache = wrapped.cache_invalidate(1, a=1)
    assert not from_cache

    await wrapped(1, a=1)
    assert wrapped.cache_info().currsize == 1

    from_cache = wrapped.cache_invalidate(1, a=1)
    assert from_cache
    assert wrapped.cache_info().currsize == 0

    await wrapped(1, a=1)
    assert wrapped.cache_info().currsize == 1

    from_cache = wrapped.cache_invalidate(1.0, a=1)
    assert from_cache
    assert wrapped.cache_info().currsize == 0


async def test_cache_clear() -> None:
    wrapped = _LRUCacheWrapper(mock.AsyncMock(return_value=1), None, True, True, None)

    await wrapped(123)

    assert wrapped.cache_info().hits == 0
    assert wrapped.cache_info().misses == 1
    assert wrapped.cache_info().currsize == 1
    assert wrapped.cache_parameters()["tasks"] == 0

    await wrapped(123)
    assert wrapped.cache_info().hits == 1
    assert wrapped.cache_info().misses == 1
    assert wrapped.cache_info().currsize == 1
    assert wrapped.cache_parameters()["tasks"] == 0

    wrapped.cache_clear()

    assert wrapped.cache_info().hits == 0
    assert wrapped.cache_info().misses == 0
    assert wrapped.cache_info().currsize == 0
    assert wrapped.cache_parameters()["tasks"] == 0


def test_cache_open() -> None:
    wrapped = _LRUCacheWrapper(mock.ANY, None, True, True, None)
    wrapped._LRUCacheWrapper__hits = 1  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__misses = 1  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__cache = {}  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__tasks = set()  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__closed = True  # type: ignore[attr-defined]

    with pytest.raises(RuntimeError):
        wrapped.cache_open()

    wrapped._LRUCacheWrapper__hits = 0  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__misses = 0  # type: ignore[attr-defined]

    wrapped.cache_open()

    assert not wrapped.cache_parameters()["closed"]

    with pytest.raises(RuntimeError):
        wrapped.cache_open()


async def test_cache_close() -> None:
    loop = asyncio.get_running_loop()
    wrapped = _LRUCacheWrapper(mock.ANY, None, True, True, None)

    awaitable = wrapped.cache_close(cancel=False, return_exceptions=True)
    await awaitable

    assert wrapped.cache_parameters()["closed"]

    with pytest.raises(RuntimeError):
        wrapped.cache_close(cancel=False, return_exceptions=True)

    fut = loop.create_future()
    wrapped._LRUCacheWrapper__closed = False  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__tasks = {fut}  # type: ignore[attr-defined]

    awaitable = wrapped.cache_close(cancel=True, return_exceptions=True)
    await awaitable

    assert fut.cancelled()

    fut = loop.create_future()
    fut.set_result(None)
    wrapped._LRUCacheWrapper__closed = False  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__tasks = {fut}  # type: ignore[attr-defined]

    awaitable = wrapped.cache_close(cancel=True, return_exceptions=True)
    await awaitable

    assert not fut.cancelled()

    fut = loop.create_future()
    fut.set_exception(ZeroDivisionError)
    wrapped._LRUCacheWrapper__closed = False  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__tasks = {fut}  # type: ignore[attr-defined]

    awaitable = wrapped.cache_close(cancel=True, return_exceptions=True)
    await awaitable

    assert not fut.cancelled()


async def test_wait_closed() -> None:
    loop = asyncio.get_running_loop()
    wrapped = _LRUCacheWrapper(mock.ANY, None, True, True, None)

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
    wrapped = _LRUCacheWrapper(mock.ANY, None, True, True, None)

    with mock.patch.object(_LRUCacheWrapper, "cache_clear") as mocked:
        wrapped._close_waited(mock.ANY)

        assert mocked.called_once()


def test_cache_info() -> None:
    wrapped = _LRUCacheWrapper(mock.ANY, 3, True, True, None)

    assert (0, 0, 3, 0) == wrapped.cache_info()

    wrapped._LRUCacheWrapper__cache[1] = 1  # type: ignore[attr-defined]

    assert (0, 0, 3, 1) == wrapped.cache_info()

    wrapped._LRUCacheWrapper__hits = 2  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__misses = 3  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__cache[2] = 2  # type: ignore[attr-defined]

    assert (2, 3, 3, 2) == wrapped.cache_info()


async def test_cache_hit() -> None:
    wrapped = _LRUCacheWrapper(mock.AsyncMock(return_value=1), None, True, True, None)
    await wrapped(1)
    assert wrapped.cache_info().hits == 0
    assert wrapped.cache_info().misses == 1
    await wrapped(1)
    assert wrapped.cache_info().hits == 1
    assert wrapped.cache_info().misses == 1
    await wrapped(1)
    assert wrapped.cache_info().hits == 2
    assert wrapped.cache_info().misses == 1


async def test_cache_miss() -> None:
    wrapped = _LRUCacheWrapper(mock.AsyncMock(return_value=1), None, True, True, None)
    await wrapped(1)
    assert wrapped.cache_info().hits == 0
    assert wrapped.cache_info().misses == 1
    await wrapped(2)
    assert wrapped.cache_info().hits == 0
    assert wrapped.cache_info().misses == 2
    await wrapped(3)
    assert wrapped.cache_info().hits == 0
    assert wrapped.cache_info().misses == 3
