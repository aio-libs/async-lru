import asyncio
import pytest

from async_lru import _CacheInfo, alru_cache


@pytest.fixture(scope='module')
def loop():
    loop = asyncio.get_event_loop()

    try:
        yield loop
    finally:
        loop.call_soon(loop.stop)
        loop.run_forever()
        loop.close()


async def _coro(val):
    return val


def test_alru_cache(loop):
    cached_coro = alru_cache(fn=_coro, maxsize=3)

    input_data = [1, 2, 3]
    coros = [cached_coro(v) for v in input_data]
    loop.run_until_complete(asyncio.gather(*coros))

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=3,
    )
    assert cached_coro.cache_info() == expected

    cached_coro.cache_clear()
    input_data = [1, 1, 1]
    coros = [cached_coro(v) for v in input_data]
    loop.run_until_complete(asyncio.gather(*coros))

    expected = _CacheInfo(
        hits=2,
        misses=1,
        maxsize=3,
        currsize=1,
    )
    assert cached_coro.cache_info() == expected

    cached_coro.cache_clear()
    input_data = [1, 2, 3, 4, 1, 2, 3, 4]
    coros = [cached_coro(v) for v in input_data]
    loop.run_until_complete(asyncio.gather(*coros))

    expected = _CacheInfo(
        hits=0,
        misses=8,
        maxsize=3,
        currsize=3,
    )
    assert cached_coro.cache_info() == expected


def test_alru_cache_none_max_size(loop):
    cached_coro = alru_cache(fn=_coro, maxsize=None)

    input_data = [1, 2, 3, 4] * 2
    coros = [cached_coro(v) for v in input_data]
    loop.run_until_complete(asyncio.gather(*coros))

    expected = _CacheInfo(
        hits=4,
        misses=4,
        maxsize=None,
        currsize=4,
    )
    assert cached_coro.cache_info() == expected


def test_alru_cache_zero_max_size():
    loop = asyncio.get_event_loop()
    cached_coro = alru_cache(fn=_coro, maxsize=0)

    input_data = [1, 2, 3, 4] * 2
    coros = [cached_coro(v) for v in input_data]
    loop.run_until_complete(asyncio.gather(*coros))

    expected = _CacheInfo(
        hits=0,
        misses=8,
        maxsize=0,
        currsize=0,
    )
    assert cached_coro.cache_info() == expected


def test_alru_cache_clear():
    loop = asyncio.get_event_loop()
    cached_coro = alru_cache(fn=_coro, maxsize=3)

    input_data = [1, 2, 3]
    coros = [cached_coro(v) for v in input_data]
    loop.run_until_complete(asyncio.gather(*coros))

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=3,
    )
    assert cached_coro.cache_info() == expected

    cached_coro.cache_clear()
    expected = _CacheInfo(
        hits=0,
        misses=0,
        maxsize=3,
        currsize=0,
    )
    assert cached_coro.cache_info() == expected


def test_alru_cache_invalidate():
    loop = asyncio.get_event_loop()
    cached_coro = alru_cache(fn=_coro, maxsize=3)

    input_data = [1, 2, 3]
    coros = [cached_coro(v) for v in input_data]
    loop.run_until_complete(asyncio.gather(*coros))

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=3,
    )
    assert cached_coro.cache_info() == expected

    cached_coro.invalidate(1)
    cached_coro.invalidate(2)
    cached_coro.invalidate(3)

    input_data = [1, 2, 3]
    coros = [cached_coro(v) for v in input_data]
    loop.run_until_complete(asyncio.gather(*coros))

    expected = _CacheInfo(
        hits=0,
        misses=6,
        maxsize=3,
        currsize=3,
    )
    assert cached_coro.cache_info() == expected
