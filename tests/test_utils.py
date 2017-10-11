import asyncio
from functools import partial
from unittest import mock

from async_lru import create_future, unpartial


def test_create_future(loop):
    loop.create_future = mock.Mock()
    loop.create_future.side_effect = AttributeError

    fut = create_future(loop=loop)

    assert isinstance(fut, asyncio.Future)

    def _create_future():
        return asyncio.Future(loop=loop)

    loop.create_future = _create_future

    fut = create_future(loop=loop)

    assert isinstance(fut, asyncio.Future)


def test_unpartial():
    def foo():
        pass

    assert unpartial(foo) is foo

    bar = partial(foo)

    assert unpartial(bar) is foo

    for _ in range(10):
        bar = partial(bar)

    assert unpartial(bar) is foo
