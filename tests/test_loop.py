import asyncio
from functools import partial

import pytest

from async_lru import alru_cache


def test_default_loop(loop):
    asyncio.set_event_loop(loop)

    @alru_cache
    @asyncio.coroutine
    def coro():
        return 1

    fut = coro()

    assert fut._loop is loop

    ret = loop.run_until_complete(coro.close())

    assert ret == [1]


@pytest.mark.asyncio
@asyncio.coroutine
def test_explicit_loop(loop):
    @alru_cache
    @asyncio.coroutine
    def coro():
        return 1

    fut = coro()

    assert fut._loop is loop

    ret = yield from coro.close(loop=loop)

    assert ret == [1]


@pytest.mark.asyncio
@asyncio.coroutine
def test_kwargs_loop(loop):
    @alru_cache(kwargs=True, loop='_loop')
    @asyncio.coroutine
    def coro(*, _loop):
        return 1

    fut = coro(_loop=loop)

    assert fut._loop is loop

    ret = yield from coro.close(loop=loop)

    assert ret == [1]


@pytest.mark.asyncio
@asyncio.coroutine
def test_cls_loop(loop):
    class Obj:
        def __init__(self, *, loop):
            self._loop = loop

        @alru_cache(cls=True, loop='_loop')
        @asyncio.coroutine
        def coro(self):
            return 1

    obj = Obj(loop=loop)

    fut = obj.coro()

    assert fut._loop is loop

    ret = yield from obj.coro.close(loop=loop)

    assert ret == [1]


@pytest.mark.asyncio
@asyncio.coroutine
def test_cls_loop_partial(loop):
    class Obj:
        def __init__(self, *, loop):
            self._loop = loop
            deco = alru_cache(cls=True, loop='_loop')
            self.coro = deco(partial(self._coro))

        @asyncio.coroutine
        def _coro(self):
            return 1

    obj = Obj(loop=loop)

    fut = obj.coro()

    assert fut._loop is loop

    ret = yield from obj.coro.close(loop=loop)

    assert ret == [1]
