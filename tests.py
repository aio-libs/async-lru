import asyncio

import pytest

from async_lru import _CacheInfo, alru_cache


@pytest.fixture(scope='module')
def loop():
    asyncio.set_event_loop(None)
    loop = asyncio.new_event_loop()

    try:
        yield loop
    finally:
        loop.call_soon(loop.stop)
        loop.run_forever()
        loop.close()


async def _coro(val):
    return val


def test_basic_alru_cache(loop):
    cached_coro = alru_cache(fn=_coro, maxsize=3, loop=loop)

    input_data = [1, 2, 3]
    coros = [cached_coro(v) for v in input_data]
    ret = loop.run_until_complete(asyncio.gather(*coros, loop=loop))

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=3,
    )
    assert cached_coro.cache_info() == expected
    assert len(cached_coro.cache) == len(input_data)
    assert len(cached_coro.coros) == 0
    assert ret == input_data

    cached_coro.cache_clear()
    input_data = [1, 1, 1]
    coros = [cached_coro(v) for v in input_data]
    ret = loop.run_until_complete(asyncio.gather(*coros, loop=loop))

    expected = _CacheInfo(
        hits=2,
        misses=1,
        maxsize=3,
        currsize=1,
    )
    assert cached_coro.cache_info() == expected
    assert len(cached_coro.cache) == 1
    assert len(cached_coro.coros) == 0
    assert ret == input_data

    cached_coro.cache_clear()
    input_data = [1, 2, 3, 4] * 2
    coros = [cached_coro(v) for v in input_data]
    ret = loop.run_until_complete(asyncio.gather(*coros, loop=loop))

    expected = _CacheInfo(
        hits=0,
        misses=8,
        maxsize=3,
        currsize=3,
    )
    assert cached_coro.cache_info() == expected
    assert len(cached_coro.cache) == 3
    assert len(cached_coro.coros) == 0
    assert ret == input_data


def test_coros_waiting_same_value(loop):
    check_list = []

    async def _coro(v):
        check_list.append(v)
        return v

    cached_coro = alru_cache(fn=_coro, maxsize=1, loop=loop)

    input_data = [7, 7, 7, 7, 7]
    coros = [cached_coro(v) for v in input_data]
    ret = loop.run_until_complete(asyncio.gather(*coros, loop=loop))

    assert check_list == [7, ]
    assert len(cached_coro.coros) == 0
    assert ret == input_data


def test_removing_lru_keys(loop):
    cached_coro = alru_cache(fn=_coro, maxsize=3, loop=loop)

    input_data = [1, 2, 3, 4, 5]
    coros = [cached_coro(v) for v in input_data]
    ret = loop.run_until_complete(asyncio.gather(*coros, loop=loop))

    expected = {3, 4, 5}
    assert set(cached_coro.cache) == expected
    assert len(cached_coro.coros) == 0
    assert ret == input_data


def test_lru_cache_wait_closed(loop):
    cached_coro = alru_cache(fn=_coro, maxsize=3, loop=loop)
    input_data = [1, 2, 3, 4, 5]
    _ = [cached_coro(v) for v in input_data]

    loop.run_until_complete(cached_coro.wait_closed(loop=loop))

    assert cached_coro.closing is False

    expected = _CacheInfo(
        hits=0,
        misses=5,
        maxsize=3,
        currsize=3,
    )
    assert cached_coro.cache_info() == expected
    assert len(cached_coro.coros) == 0


def test_lru_cache_close(loop):
    cached_coro = alru_cache(fn=_coro, maxsize=3, loop=loop)
    input_data = [1, 2, 3, 4, 5]
    _ = [cached_coro(v) for v in input_data]

    cached_coro.close()

    assert cached_coro.closing is True

    with pytest.raises(RuntimeError):
        cached_coro()

    with pytest.raises(RuntimeError):
        cached_coro.close()



def test_alru_cache_none_max_size(loop):
    cached_coro = alru_cache(fn=_coro, maxsize=None, loop=loop)

    input_data = [1, 2, 3, 4] * 2
    coros = [cached_coro(v) for v in input_data]
    ret = loop.run_until_complete(asyncio.gather(*coros, loop=loop))

    expected = _CacheInfo(
        hits=4,
        misses=4,
        maxsize=None,
        currsize=4,
    )
    assert cached_coro.cache_info() == expected
    assert len(cached_coro.cache) == len(input_data) / 2
    assert len(cached_coro.coros) == 0
    assert ret == input_data


def test_alru_cache_zero_max_size(loop):
    cached_coro = alru_cache(fn=_coro, maxsize=0, loop=loop)

    input_data = [1, 2, 3, 4] * 2
    coros = [cached_coro(v) for v in input_data]
    ret = loop.run_until_complete(asyncio.gather(*coros, loop=loop))

    expected = _CacheInfo(
        hits=0,
        misses=8,
        maxsize=0,
        currsize=0,
    )
    assert cached_coro.cache_info() == expected
    assert len(cached_coro.cache) == 0
    assert len(cached_coro.coros) == 0
    assert ret == input_data


def test_alru_cache_clear(loop):
    cached_coro = alru_cache(fn=_coro, maxsize=3, loop=loop)

    input_data = [1, 2, 3]
    coros = [cached_coro(v) for v in input_data]
    ret = loop.run_until_complete(asyncio.gather(*coros, loop=loop))

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=3,
    )
    assert cached_coro.cache_info() == expected
    assert len(cached_coro.cache) == len(input_data)
    assert len(cached_coro.coros) == 0
    assert ret == input_data

    cached_coro.cache_clear()
    expected = _CacheInfo(
        hits=0,
        misses=0,
        maxsize=3,
        currsize=0,
    )
    assert cached_coro.cache_info() == expected
    assert len(cached_coro.cache) == 0


def test_alru_cache_invalidate(loop):
    cached_coro = alru_cache(fn=_coro, maxsize=3, loop=loop)

    input_data = [1, 2, 3]
    coros = [cached_coro(v) for v in input_data]
    ret = loop.run_until_complete(asyncio.gather(*coros, loop=loop))

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=3,
    )
    assert cached_coro.cache_info() == expected
    assert len(cached_coro.cache) == len(input_data)
    assert len(cached_coro.coros) == 0
    assert ret == input_data

    cached_coro.invalidate(1)
    cached_coro.invalidate(2)
    cached_coro.invalidate(3)

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=0,
    )
    assert cached_coro.cache_info() == expected
    assert len(cached_coro.cache) == 0

    input_data = [1, 2, 3]
    coros = [cached_coro(v) for v in input_data]
    ret = loop.run_until_complete(asyncio.gather(*coros, loop=loop))

    expected = _CacheInfo(
        hits=0,
        misses=6,
        maxsize=3,
        currsize=3,
    )
    assert cached_coro.cache_info() == expected
    assert len(cached_coro.cache) == len(input_data)
    assert len(cached_coro.coros) == 0
    assert ret == input_data
