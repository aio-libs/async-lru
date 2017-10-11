import asyncio

import pytest

from async_lru import _get_loop


def test_get_loop_no_default_loop():
    asyncio.set_event_loop(None)

    args = [None, None, None, None, None]

    with pytest.raises(RuntimeError):
        _get_loop(*args, loop=None)


def test_get_loop_default_loop(loop):
    asyncio.set_event_loop(loop)

    args = [None, None, None, None, None]

    _loop = _get_loop(*args, loop=None)

    assert _loop is loop


def test_get_loop_explicit(loop):
    args = [None, None, None, None, None]

    _loop = _get_loop(*args, loop=loop)

    assert _loop is loop


def test_get_loop_str_cls_kwargs():
    args = [True, True, None, None, None]

    with pytest.raises(AssertionError):
        _get_loop(*args, loop='_loop')


def test_get_loop_kwargs(loop):
    args = [False, True, None, None, {'_loop': loop}]

    _loop = _get_loop(*args, loop='_loop')

    assert _loop is loop

    args[4].pop('_loop')

    with pytest.raises(KeyError):
        _get_loop(*args, loop='_loop')


def test_get_loop_cls(loop):
    class Obj:
        def __init__(self, *, loop):
            self._loop = loop

        async def coro(self):
            pass

    obj = Obj(loop=loop)

    args = [True, False, obj.coro, None, None]

    _loop = _get_loop(*args, loop='_loop')

    assert _loop is loop

    with pytest.raises(AttributeError):
        _get_loop(*args, loop='loop')

    args[2] = Obj.coro
    args[3] = [obj]

    _loop = _get_loop(*args, loop='_loop')

    assert _loop is loop

    args[3] = []

    with pytest.raises(AssertionError):
        _get_loop(*args, loop='_loop')
