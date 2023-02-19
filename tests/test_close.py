import asyncio
from typing import Callable

import pytest

from async_lru import alru_cache


async def test_cache_close(check_lru: Callable[..., None]) -> None:
    @alru_cache()
    async def coro(val: int) -> int:
        await asyncio.sleep(0.2)

        return val

    assert not coro.cache_parameters()["closed"]

    inputs = [1, 2, 3, 4, 5]

    coros = [coro(v) for v in inputs]

    gather = asyncio.gather(*coros)

    await asyncio.sleep(0.1)

    check_lru(coro, hits=0, misses=5, cache=5, tasks=5)

    close = coro.close()

    with pytest.raises(RuntimeError):
        await coro(1)

    check_lru(coro, hits=0, misses=5, cache=5, tasks=5)

    ret_close = await close

    check_lru(coro, hits=0, misses=0, cache=0, tasks=0)

    ret_gather = await gather

    check_lru(coro, hits=0, misses=0, cache=0, tasks=0)

    assert set(ret_close) == set(ret_gather) == set(inputs)

    with pytest.raises(RuntimeError):
        coro.close()


async def test_cache_close_cancel_return_exceptions(
    check_lru: Callable[..., None]
) -> None:
    @alru_cache()
    async def coro(val: int) -> int:
        await asyncio.sleep(0.2)

        return val

    inputs = [1, 2, 3, 4, 5]

    coros = [coro(v) for v in inputs]

    gather = asyncio.gather(*coros)

    await asyncio.sleep(0.1)

    close = coro.close(cancel=True)

    check_lru(coro, hits=0, misses=5, cache=5, tasks=5)

    ret_close = await close

    check_lru(coro, hits=0, misses=0, cache=0, tasks=0)

    for err in ret_close:
        assert isinstance(err, asyncio.CancelledError)

    with pytest.raises(asyncio.CancelledError):
        await gather


async def test_cache_close_cancel_not_return_exceptions(
    check_lru: Callable[..., None]
) -> None:
    @alru_cache()
    async def coro(val: int) -> int:
        await asyncio.sleep(0.2)

        return val

    inputs = [1, 2, 3, 4, 5]

    coros = [coro(v) for v in inputs]

    gather = asyncio.gather(*coros)

    await asyncio.sleep(0.1)

    close = coro.close(cancel=True, return_exceptions=False)

    check_lru(coro, hits=0, misses=5, cache=5, tasks=5)

    with pytest.raises(asyncio.CancelledError):
        await close

    with pytest.raises(asyncio.CancelledError):
        await gather

    check_lru(coro, hits=0, misses=0, cache=0, tasks=0)


async def test_cache_close_return_exceptions(check_lru: Callable[..., None]) -> None:
    @alru_cache
    async def coro(val: int) -> int:
        await asyncio.sleep(0.2)

        raise ZeroDivisionError

    inputs = [1, 2, 3, 4, 5]

    coros = [coro(v) for v in inputs]

    gather = asyncio.gather(*coros)

    await asyncio.sleep(0.1)

    close = coro.close()

    check_lru(coro, hits=0, misses=5, cache=5, tasks=5)

    with pytest.raises(ZeroDivisionError):
        await gather

    check_lru(coro, hits=0, misses=5, cache=5, tasks=0)

    ret_close = await close

    check_lru(coro, hits=0, misses=0, cache=0, tasks=0)

    for err in ret_close:
        assert isinstance(err, ZeroDivisionError)

    check_lru(coro, hits=0, misses=0, cache=0, tasks=0)


async def test_cache_close_not_return_exceptions(
    check_lru: Callable[..., None]
) -> None:
    @alru_cache()
    async def coro(val: int) -> int:
        await asyncio.sleep(0.2)

        raise ZeroDivisionError

    inputs = [1, 2, 3, 4, 5]

    coros = [coro(v) for v in inputs]

    gather = asyncio.gather(*coros, return_exceptions=True)

    await asyncio.sleep(0.1)

    close = coro.close(return_exceptions=False)

    check_lru(coro, hits=0, misses=5, cache=5, tasks=5)

    with pytest.raises(ZeroDivisionError):
        await close

    check_lru(coro, hits=0, misses=0, cache=0, tasks=0)

    ret_gather = await gather

    for err in ret_gather:
        assert isinstance(err, ZeroDivisionError)

    check_lru(coro, hits=0, misses=0, cache=0, tasks=0)
