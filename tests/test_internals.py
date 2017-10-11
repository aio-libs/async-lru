from asyncio import test_utils
from functools import _make_key, partial

import pytest
from async_lru import _cache_invalidate, _done_callback, create_future


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


# def _cache_clear

# def _open

# def _close

# def _wait_closed

# def __wait_closed

# def __cache_info

# def __cache_touch

# def _cache_hit

# def _cache_miss
