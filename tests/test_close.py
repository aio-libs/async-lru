import asyncio

import pytest

from async_lru import alru_cache

pytestmark = pytest.mark.asyncio


async def test_cache_close(loop):

    @alru_cache(loop=loop)
    async def coro(val):
        await asyncio.sleep(0.2, loop=loop)

        return val

    assert not coro.closed

    inputs = [1, 2, 3, 4, 5]

    coros = [coro(v) for v in inputs]

    gather = asyncio.gather(*coros, loop=loop)

    await asyncio.sleep(0.1, loop=loop)

    assert len(coro.tasks) == 5

    close = coro.close(loop=loop)

    with pytest.raises(RuntimeError):
        await coro(1)

    assert len(coro.tasks) == 5

    ret_close = await close

    assert len(coro.tasks) == 0

    ret_gather = await gather

    assert len(coro.tasks) == 0

    assert set(ret_close) == set(ret_gather) == set(inputs)

    with pytest.raises(RuntimeError):
        coro.close(loop=loop)


async def test_cache_close_cancel_return_exceptions(loop):
    @alru_cache(loop=loop)
    async def coro(val):
        await asyncio.sleep(0.2, loop=loop)

        return val

    inputs = [1, 2, 3, 4, 5]

    coros = [coro(v) for v in inputs]

    gather = asyncio.gather(*coros, loop=loop)

    await asyncio.sleep(0.1, loop=loop)

    close = coro.close(cancel=True, loop=loop)

    ret_close = await close

    for err in ret_close:
        assert isinstance(err, asyncio.CancelledError)

    with pytest.raises(asyncio.CancelledError):
        await gather


async def test_cache_close_cancel_not_return_exceptions(loop):
    @alru_cache(loop=loop)
    async def coro(val):
        await asyncio.sleep(0.2, loop=loop)

        return val

    inputs = [1, 2, 3, 4, 5]

    coros = [coro(v) for v in inputs]

    gather = asyncio.gather(*coros, loop=loop)

    await asyncio.sleep(0.1, loop=loop)

    close = coro.close(cancel=True, return_exceptions=False, loop=loop)

    with pytest.raises(asyncio.CancelledError):
        await close

    with pytest.raises(asyncio.CancelledError):
        await gather


async def test_cache_close_return_exceptions(loop):
    @alru_cache(loop=loop)
    async def coro(val):
        await asyncio.sleep(0.2, loop=loop)

        raise ZeroDivisionError

    inputs = [1, 2, 3, 4, 5]

    coros = [coro(v) for v in inputs]

    gather = asyncio.gather(*coros, loop=loop)

    await asyncio.sleep(0.1, loop=loop)

    close = coro.close(loop=loop)

    with pytest.raises(ZeroDivisionError):
        await gather

    ret_close = await close

    for err in ret_close:
        assert isinstance(err, ZeroDivisionError)


async def test_cache_close_not_return_exceptions(loop):
    @alru_cache(loop=loop)
    async def coro(val):
        await asyncio.sleep(0.2, loop=loop)

        raise ZeroDivisionError

    inputs = [1, 2, 3, 4, 5]

    coros = [coro(v) for v in inputs]

    gather = asyncio.gather(*coros, return_exceptions=True, loop=loop)

    await asyncio.sleep(0.1, loop=loop)

    close = coro.close(return_exceptions=False, loop=loop)

    with pytest.raises(ZeroDivisionError):
        await close

    ret_gather = await gather

    for err in ret_gather:
        assert isinstance(err, ZeroDivisionError)
