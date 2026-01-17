import asyncio
import logging
from functools import partial
from unittest import mock

import pytest

from async_lru import _CacheItem, _LRUCacheWrapper


async def test_done_callback_cancelled() -> None:
    wrapped = _LRUCacheWrapper(mock.ANY, None, False, None)
    loop = asyncio.get_running_loop()
    task = loop.create_future()

    key = 1

    task.add_done_callback(partial(wrapped._task_done_callback, key))

    task.cancel()

    await asyncio.sleep(0)

    assert task not in wrapped._LRUCacheWrapper__tasks  # type: ignore[attr-defined]


async def test_done_callback_exception() -> None:
    wrapped = _LRUCacheWrapper(mock.ANY, None, False, None)
    loop = asyncio.get_running_loop()
    task = loop.create_future()

    key = 1

    task.add_done_callback(partial(wrapped._task_done_callback, key))

    exc = ZeroDivisionError()

    task.set_exception(exc)

    await asyncio.sleep(0)

    assert task not in wrapped._LRUCacheWrapper__tasks  # type: ignore[attr-defined]


async def test_done_callback_exception_logs(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.ERROR, logger="asyncio")

    wrapped = _LRUCacheWrapper(mock.ANY, None, False, None)
    loop = asyncio.get_running_loop()

    async def boom() -> None:
        await asyncio.sleep(0)
        raise RuntimeError("boom")

    key = object()
    task = loop.create_task(boom())
    wrapped._LRUCacheWrapper__cache[key] = _CacheItem(task, None, 1)  # type: ignore[attr-defined]
    task.add_done_callback(partial(wrapped._task_done_callback, key))

    while not task.done():
        await asyncio.sleep(0)
    await asyncio.sleep(0)

    assert key not in wrapped._LRUCacheWrapper__cache  # type: ignore[attr-defined]
    # asyncio disables logging when exception() is called; keep logging enabled.
    assert task._log_traceback  # type: ignore[attr-defined]


async def test_cache_invalidate_typed() -> None:
    wrapped = _LRUCacheWrapper(mock.AsyncMock(return_value=1), None, True, None)

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
    wrapped = _LRUCacheWrapper(mock.AsyncMock(return_value=1), None, False, None)

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
    wrapped = _LRUCacheWrapper(mock.AsyncMock(return_value=1), None, True, None)

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


def test_cache_info() -> None:
    wrapped = _LRUCacheWrapper(mock.ANY, 3, True, None)

    assert (0, 0, 3, 0) == wrapped.cache_info()

    wrapped._LRUCacheWrapper__cache[1] = 1  # type: ignore[attr-defined]

    assert (0, 0, 3, 1) == wrapped.cache_info()

    wrapped._LRUCacheWrapper__hits = 2  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__misses = 3  # type: ignore[attr-defined]
    wrapped._LRUCacheWrapper__cache[2] = 2  # type: ignore[attr-defined]

    assert (2, 3, 3, 2) == wrapped.cache_info()


async def test_cache_hit() -> None:
    wrapped = _LRUCacheWrapper(mock.AsyncMock(return_value=1), None, True, None)
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
    wrapped = _LRUCacheWrapper(mock.AsyncMock(return_value=1), None, True, None)
    await wrapped(1)
    assert wrapped.cache_info().hits == 0
    assert wrapped.cache_info().misses == 1
    await wrapped(2)
    assert wrapped.cache_info().hits == 0
    assert wrapped.cache_info().misses == 2
    await wrapped(3)
    assert wrapped.cache_info().hits == 0
    assert wrapped.cache_info().misses == 3


async def test_forbid_call_closed() -> None:
    wrapped = _LRUCacheWrapper(mock.AsyncMock(return_value=1), None, True, None)
    wrapped._LRUCacheWrapper__closed = True  # type: ignore[attr-defined]
    with pytest.raises(RuntimeError):
        await wrapped(123)
