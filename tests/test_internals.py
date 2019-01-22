import asyncio
from collections import OrderedDict
from functools import _make_key, partial
from unittest import mock

import pytest

from async_lru import (__cache_touch, _cache_clear, _cache_hit, _cache_info,
                       _cache_invalidate, _cache_miss, _close, _close_waited,
                       _done_callback, _open, _wait_closed, create_future)

try:
    from asyncio import test_utils
except ImportError:
    from test.test_asyncio import utils as test_utils


class Wrapped:
    pass


def test_done_callback_cancelled(loop):
    task = create_future(loop=loop)
    fut = create_future(loop=loop)

    task.add_done_callback(partial(_done_callback, fut))

    task.cancel()

    test_utils.run_briefly(loop)

    assert fut.cancelled()


def test_done_callback_exception(loop):
    task = create_future(loop=loop)
    fut = create_future(loop=loop)

    task.add_done_callback(partial(_done_callback, fut))

    exc = ZeroDivisionError()

    task.set_exception(exc)

    test_utils.run_briefly(loop)

    with pytest.raises(ZeroDivisionError):
        loop.run_until_complete(fut)

    with pytest.raises(ZeroDivisionError):
        fut.result()

    assert fut.exception() is exc


def test_done_callback(loop):
    task = create_future(loop=loop)
    fut = create_future(loop=loop)

    task.add_done_callback(partial(_done_callback, fut))

    task.set_result(1)

    test_utils.run_briefly(loop)

    assert fut.result() == 1


def test_cache_invalidate_typed():
    wrapped = Wrapped()
    wrapped._cache = {}

    args = (1,)
    kwargs = {'1': 1}

    from_cache = _cache_invalidate(wrapped, True, *args, **kwargs)

    assert not from_cache

    key = _make_key(args, kwargs, True)

    wrapped._cache[key] = 0

    from_cache = _cache_invalidate(wrapped, True, *args, **kwargs)

    assert from_cache

    assert len(wrapped._cache) == 0

    wrapped._cache[key] = 0

    args = (1.0,)

    from_cache = _cache_invalidate(wrapped, True, *args, **kwargs)

    assert not from_cache

    wrapped._cache[key] = 1


def test_cache_invalidate_not_typed():
    wrapped = Wrapped()
    wrapped._cache = {}

    args = (1,)
    kwargs = {'1': 1}

    from_cache = _cache_invalidate(wrapped, False, *args, **kwargs)

    assert not from_cache

    key = _make_key(args, kwargs, False)

    wrapped._cache[key] = 0

    from_cache = _cache_invalidate(wrapped, False, *args, **kwargs)

    assert from_cache

    assert len(wrapped._cache) == 0

    wrapped._cache[key] = 0

    args = (1.0,)

    from_cache = _cache_invalidate(wrapped, False, *args, **kwargs)

    assert from_cache

    assert len(wrapped._cache) == 0


def test_cache_clear():
    wrapped = Wrapped()

    attrs = ['hits', '_cache', 'tasks']
    for attr in attrs:
        assert not hasattr(wrapped, attr)

    _cache_clear(wrapped)

    for attr in attrs:
        assert hasattr(wrapped, attr)

    assert wrapped.hits == wrapped.misses == 0
    assert isinstance(wrapped._cache, dict)
    assert len(wrapped._cache) == 0
    assert isinstance(wrapped.tasks, set)
    assert len(wrapped.tasks) == 0

    _cache = wrapped._cache
    tasks = wrapped.tasks

    _cache_clear(wrapped)

    assert wrapped._cache is not _cache
    assert wrapped.tasks is not tasks


def test_open():
    wrapped = Wrapped()
    wrapped.hits = wrapped.misses = 1
    wrapped._cache = {}
    wrapped.tasks = set()
    wrapped.closed = True

    with pytest.raises(RuntimeError):
        _open(wrapped)

    wrapped.hits = wrapped.misses = 0

    _open(wrapped)

    assert not wrapped.closed

    with pytest.raises(RuntimeError):
        _open(wrapped)


def test_close(loop):
    wrapped = Wrapped()
    wrapped.closed = False
    wrapped.tasks = set()

    _close(
        wrapped,
        cancel=False,
        return_exceptions=True,
        loop=None
    )

    assert wrapped.closed

    with pytest.raises(RuntimeError):
        _close(
            wrapped,
            cancel=False,
            return_exceptions=True,
            loop=None
        )

    fut = create_future(loop=loop)
    wrapped.closed = False
    wrapped.tasks = {fut}

    _close(
        wrapped,
        cancel=True,
        return_exceptions=True,
        loop=None
    )

    assert fut.cancelled()

    fut = create_future(loop=loop)
    fut.set_result(None)
    wrapped.closed = False
    wrapped.tasks = {fut}

    _close(
        wrapped,
        cancel=True,
        return_exceptions=True,
        loop=None
    )

    assert not fut.cancelled()

    fut = create_future(loop=loop)
    fut.set_exception(ZeroDivisionError)
    wrapped.closed = False
    wrapped.tasks = {fut}

    _close(
        wrapped,
        cancel=True,
        return_exceptions=True,
        loop=None
    )

    assert not fut.cancelled()


@pytest.mark.asyncio
async def test_wait_closed(loop):
    wrapped = Wrapped()
    wrapped.tasks = set()

    with mock.patch('async_lru._close_waited') as mocked:
        ret = await _wait_closed(
            wrapped,
            return_exceptions=True,
            loop=loop,
        )
        assert ret == []
        assert mocked.called_once()

    asyncio.set_event_loop(loop)
    with mock.patch('async_lru._close_waited') as mocked:
        ret = await _wait_closed(
            wrapped,
            return_exceptions=True,
            loop=None,
        )
        assert ret == []
        assert mocked.called_once()
    asyncio.set_event_loop(None)

    fut = create_future(loop=loop)
    fut.set_result(None)
    wrapped.tasks = {fut}
    with mock.patch('async_lru._close_waited') as mocked:
        ret = await _wait_closed(
            wrapped,
            return_exceptions=True,
            loop=loop,
        )
        assert ret == [None]
        assert mocked.called_once()

    exc = ZeroDivisionError()
    fut = create_future(loop=loop)
    fut.set_exception(exc)
    wrapped.tasks = {fut}
    with mock.patch('async_lru._close_waited') as mocked:
        ret = await _wait_closed(
            wrapped,
            return_exceptions=True,
            loop=loop,
        )
        assert ret == [exc]
        assert mocked.called_once()

    fut = create_future(loop=loop)
    fut.set_exception(ZeroDivisionError)
    wrapped.tasks = {fut}
    with mock.patch('async_lru._close_waited') as mocked:
        with pytest.raises(ZeroDivisionError):
            await _wait_closed(
                wrapped,
                return_exceptions=False,
                loop=loop,
            )
        assert mocked.called_once()


def test_close_waited():
    wrapped = Wrapped()
    wrapped.cache_clear = partial(_cache_clear, wrapped)

    with mock.patch('async_lru._cache_clear') as mocked:
        _close_waited(wrapped, None)

        assert mocked.called_once()


def test_cache_info():
    wrapped = Wrapped()
    wrapped._cache = {}
    wrapped.hits = wrapped.misses = 0

    assert (0, 0, 3, 0) == _cache_info(wrapped, 3)

    wrapped._cache[1] = 1

    assert (0, 0, 1, 1) == _cache_info(wrapped, 1)

    wrapped.hits = 2
    wrapped.misses = 3
    wrapped._cache[2] = 2

    assert (2, 3, 5, 2) == _cache_info(wrapped, 5)


def test__cache_touch():
    wrapped = Wrapped()

    wrapped._cache = OrderedDict()
    wrapped._cache[1] = 1
    wrapped._cache[2] = 2

    __cache_touch(wrapped, 1)
    assert list(wrapped._cache) == [2, 1]

    __cache_touch(wrapped, 2)
    assert list(wrapped._cache) == [1, 2]

    # test KeyError
    __cache_touch(wrapped, 100)


def test_cache_hit():
    wrapped = Wrapped()
    wrapped.hits = 1
    wrapped._cache = OrderedDict()
    wrapped._cache[1] = 1

    with mock.patch('async_lru.__cache_touch') as mocked:
        _cache_hit(wrapped, 1)

        assert mocked.called_once()

    assert wrapped.hits == 2

    _cache_hit(wrapped, 1)

    assert wrapped.hits == 3


def test_cache_miss():
    wrapped = Wrapped()
    wrapped.misses = 1
    wrapped._cache = OrderedDict()
    wrapped._cache[1] = 1

    with mock.patch('async_lru.__cache_touch') as mocked:
        _cache_miss(wrapped, 1)

        assert mocked.called_once()

    assert wrapped.misses == 2

    _cache_miss(wrapped, 1)

    assert wrapped.misses == 3
