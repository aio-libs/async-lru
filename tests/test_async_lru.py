import asyncio   # noqa # isort:skip
from functools import partial

import pytest
from async_lru import _CacheInfo, alru_cache


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_basic(loop):
    @alru_cache(maxsize=4, loop=loop)
    @asyncio.coroutine
    def coro(val):
        return val

    input_data = [1, 2, 3]
    coros = [coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=4,
        currsize=3,
    )

    assert coro.cache_info() == expected
    assert len(coro.cache) == len(input_data)
    assert len(coro.coros) == 0
    assert ret == input_data

    coro.cache_clear()

    input_data = [1, 1, 1]
    coros = [coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=2,
        misses=1,
        maxsize=4,
        currsize=1,
    )

    assert coro.cache_info() == expected
    assert len(coro.cache) == 1
    assert len(coro.coros) == 0
    assert ret == input_data

    coro.cache_clear()

    input_data = [1, 2, 3, 4] * 2
    coros = [coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=4,
        misses=4,
        maxsize=4,
        currsize=4,
    )

    assert coro.cache_info() == expected
    assert len(coro.cache) == 4
    assert len(coro.coros) == 0
    assert ret == input_data


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_coros_waiting_same_value(loop):
    check_list = []

    @alru_cache(maxsize=1, loop=loop)
    @asyncio.coroutine
    def coro(val):
        check_list.append(val)
        return val

    input_data = [7, 7, 7, 7, 7]
    coros = [coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    assert check_list == [7]
    assert len(coro.coros) == 0
    assert ret == input_data

    one_more = coro(7)

    for fut in coros:
        assert fut is one_more

    ret = yield from one_more

    assert ret == 7


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_removing_lru_keys(loop):
    @alru_cache(maxsize=3, loop=loop)
    @asyncio.coroutine
    def coro(val):
        return val

    input_data = [3, 4, 5]
    coros = [coro(v) for v in input_data]

    yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=3,
    )

    assert coro.cache_info() == expected

    input_data = [3, 2, 1]
    coros = [coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=1,
        misses=5,
        maxsize=3,
        currsize=3,
    )

    assert coro.cache_info() == expected
    assert len(coro.coros) == 0
    assert ret == input_data


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_close(loop):
    calls = 0

    @alru_cache(maxsize=3, loop=loop)
    @asyncio.coroutine
    def coro(val):
        nonlocal calls

        calls += 1

        return val

    input_data = [1, 2, 3, 4, 5]
    [coro(v) for v in input_data]

    assert coro.closed is False

    assert calls == 0

    expected = _CacheInfo(
        hits=0,
        misses=5,
        maxsize=3,
        currsize=3,
    )

    assert coro.cache_info() == expected

    yield from coro.close(loop=loop)

    assert coro.closed is True

    assert calls == 5

    expected = _CacheInfo(
        hits=0,
        misses=0,
        maxsize=3,
        currsize=0,
    )

    assert coro.cache_info() == expected
    assert len(coro.coros) == 0

    with pytest.raises(RuntimeError):
        coro()

    with pytest.raises(RuntimeError):
        yield from coro.close()


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_open(loop):
    @alru_cache(maxsize=3, loop=loop)
    @asyncio.coroutine
    def coro(val):
        return val

    assert coro.closed is False

    with pytest.raises(RuntimeError):
        coro.open()

    yield from coro.close(loop=loop)

    assert coro.closed is True

    with pytest.raises(RuntimeError):
        coro()

    coro.open()

    input_data = [3, 2, 1]
    coros = [coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=0,
        misses=0,
        maxsize=3,
        currsize=0,
    )

    assert coro.cache_info() == expected
    assert len(coro.coros) == 0
    assert ret == input_data


def test_alru_cache_no_default_event_loop(loop):
    asyncio.set_event_loop(None)

    @alru_cache
    @asyncio.coroutine
    def coro(val):
        return val

    with pytest.raises(RuntimeError):
        coro(1)


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_default_event_loop(loop):
    asyncio.set_event_loop(loop)

    @alru_cache(maxsize=3, loop=loop)
    @asyncio.coroutine
    def coro(val):
        return val

    input_data = [1, 2, 3, 4, 5]
    [coro(v) for v in input_data]

    assert coro.closed is False

    expected = _CacheInfo(
        hits=0,
        misses=5,
        maxsize=3,
        currsize=3,
    )

    assert coro.cache_info() == expected

    yield from coro.close()

    assert coro.closed is True


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_close_wait(loop):
    fut = asyncio.Future(loop=loop)

    @alru_cache(maxsize=3, loop=loop)
    @asyncio.coroutine
    def coro(val):
        yield from asyncio.sleep(.01, loop=loop)

        fut.set_result(None)

        return val

    coro(1)

    assert coro.closed is False

    expected = _CacheInfo(
        hits=0,
        misses=1,
        maxsize=3,
        currsize=1,
    )

    assert coro.cache_info() == expected

    assert not fut.done()

    yield from coro.close(loop=loop)

    assert fut.done()


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_close_cancel(loop):
    calls = 0

    @alru_cache(maxsize=3, loop=loop)
    @asyncio.coroutine
    def coro(val):
        nonlocal calls

        calls + 1

        return val

    input_data = [1, 2, 3, 4, 5]
    [coro(v) for v in input_data]

    assert coro.closed is False

    assert calls == 0

    expected = _CacheInfo(
        hits=0,
        misses=5,
        maxsize=3,
        currsize=3,
    )

    assert coro.cache_info() == expected

    yield from coro.close(cancel=True, loop=loop)

    assert coro.closed is True

    assert calls == 0

    expected = _CacheInfo(
        hits=0,
        misses=0,
        maxsize=3,
        currsize=0,
    )

    assert coro.cache_info() == expected
    assert len(coro.coros) == 0

    with pytest.raises(RuntimeError):
        coro()

    with pytest.raises(RuntimeError):
        yield from coro.close()


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_close_return_exceptions(loop):
    @alru_cache(maxsize=3, loop=loop)
    @asyncio.coroutine
    def coro(val):
        raise ZeroDivisionError

    input_data = [1, 2, 3, 4, 5]
    [coro(v) for v in input_data]

    expected = _CacheInfo(
        hits=0,
        misses=5,
        maxsize=3,
        currsize=3,
    )

    assert coro.cache_info() == expected

    close = coro.close(cancel=False, return_exceptions=True, loop=loop)

    ret = yield from close

    expected = _CacheInfo(
        hits=0,
        misses=0,
        maxsize=3,
        currsize=0,
    )

    assert coro.cache_info() == expected

    for item in ret:
        assert isinstance(item, ZeroDivisionError)

    coro.open()

    input_data = [1, 2, 3, 4, 5]
    [coro(v) for v in input_data]

    with pytest.raises(ZeroDivisionError):
        yield from coro.close(cancel=False, return_exceptions=False, loop=loop)

    coro.open()

    input_data = [1, 2, 3, 4, 5]
    [coro(v) for v in input_data]

    with pytest.raises(asyncio.CancelledError):
        yield from coro.close(cancel=True, return_exceptions=False, loop=loop)


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_none_max_size(loop):
    @alru_cache(maxsize=None, loop=loop)
    @asyncio.coroutine
    def coro(val):
        return val

    input_data = [1, 2, 3, 4] * 2
    coros = [coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=4,
        misses=4,
        maxsize=None,
        currsize=4,
    )

    assert coro.cache_info() == expected
    assert len(coro.cache) == len(input_data) // 2
    assert len(coro.coros) == 0
    assert ret == input_data


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_zero_max_size(loop):
    @alru_cache(maxsize=0, loop=loop)
    @asyncio.coroutine
    def coro(val):
        return val

    input_data = [1, 2, 3, 4] * 2
    coros = [coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=0,
        misses=8,
        maxsize=0,
        currsize=0,
    )
    assert coro.cache_info() == expected
    assert len(coro.cache) == 0
    assert len(coro.coros) == 0
    assert ret == input_data


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_clear(loop):
    @alru_cache(maxsize=3, loop=loop)
    @asyncio.coroutine
    def coro(val):
        return val

    input_data = [1, 2, 3]
    coros = [coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=3,
    )

    assert coro.cache_info() == expected
    assert len(coro.cache) == len(input_data)
    assert len(coro.coros) == 0
    assert ret == input_data

    coro.cache_clear()

    expected = _CacheInfo(
        hits=0,
        misses=0,
        maxsize=3,
        currsize=0,
    )

    assert coro.cache_info() == expected
    assert len(coro.cache) == 0


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_invalidate(loop):
    @alru_cache(maxsize=3, loop=loop)
    @asyncio.coroutine
    def coro(val):
        return val

    input_data = [1, 2, 3]

    coro.invalidate(1)
    coro.invalidate(2)
    coro.invalidate(3)

    coros = [coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=3,
    )

    assert coro.cache_info() == expected
    assert len(coro.cache) == len(input_data)
    assert len(coro.coros) == 0
    assert ret == input_data

    coro.invalidate(1)
    coro.invalidate(2)
    coro.invalidate(3)

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=0,
    )

    assert coro.cache_info() == expected
    assert len(coro.cache) == 0

    input_data = [1, 2, 3]
    coros = [coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=0,
        misses=6,
        maxsize=3,
        currsize=3,
    )

    assert coro.cache_info() == expected
    assert len(coro.cache) == len(input_data)
    assert len(coro.coros) == 0
    assert ret == input_data


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_decorator(loop):
    @alru_cache(maxsize=3, loop=loop)
    @asyncio.coroutine
    def coro(val):
        return val

    input_data = [1, 2, 3]
    coros = [coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=3,
    )

    assert coro.cache_info() == expected
    assert len(coro.cache) == len(input_data)
    assert len(coro.coros) == 0
    assert ret == input_data


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_decorator_simple(loop):
    asyncio.set_event_loop(loop)

    @alru_cache
    @asyncio.coroutine
    def coro(val):
        return val

    input_data = [1, 2, 3]
    coros = [coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=128,
        currsize=3,
    )

    assert coro.cache_info() == expected
    assert len(coro.cache) == len(input_data)
    assert len(coro.coros) == 0
    assert ret == input_data


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_funcion(loop):
    @asyncio.coroutine
    def _coro(val):
        return val

    coro = alru_cache(maxsize=3, loop=loop)(_coro)

    input_data = [1, 2, 3]
    coros = [coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=3,
    )

    assert coro.cache_info() == expected
    assert len(coro.cache) == len(input_data)
    assert len(coro.coros) == 0
    assert ret == input_data


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_funcion_fn(loop):
    @asyncio.coroutine
    def _coro(val):
        return val

    coro = alru_cache(fn=_coro, maxsize=3, loop=loop)

    input_data = [1, 2, 3]
    coros = [coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=3,
    )

    assert coro.cache_info() == expected
    assert len(coro.cache) == len(input_data)
    assert len(coro.coros) == 0
    assert ret == input_data


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_not_callable(loop):
    with pytest.raises(NotImplementedError):
        alru_cache('foo')


def test_alru_cache_not_coroutine(loop):
    with pytest.raises(RuntimeError):
        @alru_cache
        def not_coro(val):
            return val


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_loop_kwargs(loop):
    @alru_cache(maxsize=3, kwargs=True, loop='loop')
    @asyncio.coroutine
    def coro(val, *, loop):
        return val

    input_data = [1, 2, 3]
    coros = [coro(v, loop=loop) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=3,
    )

    assert coro.cache_info() == expected
    assert len(coro.cache) == len(input_data)
    assert len(coro.coros) == 0
    assert ret == input_data

    class C:
        @alru_cache(maxsize=3, kwargs=True, loop='loop')
        @asyncio.coroutine
        def coro(self, val, *, loop):
            return val

    c = C()
    input_data = [1, 2, 3]
    coros = [c.coro(v, loop=loop) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=3,
    )

    assert c.coro.cache_info() == expected
    assert len(c.coro.cache) == len(input_data)
    assert len(c.coro.coros) == 0
    assert ret == input_data


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_loop_cls(loop):
    class C:
        def __init__(self, *, loop):
            self.loop = loop

        @alru_cache(maxsize=3, cls=True, loop='loop')
        @asyncio.coroutine
        def coro(self, val):
            return val

    c = C(loop=loop)
    input_data = [1, 2, 3]
    coros = [c.coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=3,
    )

    assert c.coro.cache_info() == expected
    assert len(c.coro.cache) == len(input_data)
    assert len(c.coro.coros) == 0
    assert ret == input_data

    class C:
        def __init__(self, *, loop):
            self.loop = loop
            deco = alru_cache(maxsize=3, cls=True, loop='loop')
            self.coro = deco(self._coro)

        @asyncio.coroutine
        def _coro(self, val):
            return val

    c = C(loop=loop)
    input_data = [1, 2, 3]
    coros = [c.coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=3,
    )

    assert c.coro.cache_info() == expected
    assert len(c.coro.cache) == len(input_data)
    assert len(c.coro.coros) == 0
    assert ret == input_data

    class C:
        def __init__(self, *, loop):
            self.loop = loop
            coro = partial(self._coro)
            self.coro = alru_cache(maxsize=3, cls=True, loop='loop')(coro)

        @asyncio.coroutine
        def _coro(self, val):
            return val

    c = C(loop=loop)
    input_data = [1, 2, 3]
    coros = [c.coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=3,
    )

    assert c.coro.cache_info() == expected
    assert len(c.coro.cache) == len(input_data)
    assert len(c.coro.coros) == 0
    assert ret == input_data


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_funcion_partial(loop):
    @asyncio.coroutine
    def _coro(val):
        return val

    coro = alru_cache(maxsize=3, loop=loop)(partial(_coro))

    input_data = [1, 2, 3]
    coros = [coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop)

    expected = _CacheInfo(
        hits=0,
        misses=3,
        maxsize=3,
        currsize=3,
    )

    assert coro.cache_info() == expected
    assert len(coro.cache) == len(input_data)
    assert len(coro.coros) == 0
    assert ret == input_data


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_exception(loop):
    @alru_cache(maxsize=3, cache_exceptions=True, loop=loop)
    @asyncio.coroutine
    def coro(val):
        1/0

    input_data = [1, 1, 1]
    coros = [coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop, return_exceptions=True)

    expected = _CacheInfo(
        hits=2,
        misses=1,
        maxsize=3,
        currsize=1,
    )

    assert coro.cache_info() == expected
    assert len(coro.cache) == 1
    assert len(coro.coros) == 0
    for item in ret:
        assert isinstance(item, ZeroDivisionError)

    one_more = coro(1)

    for fut in coros:
        assert fut is one_more

    with pytest.raises(ZeroDivisionError):
        yield from one_more

    @alru_cache(maxsize=3, cache_exceptions=False, loop=loop)
    @asyncio.coroutine
    def coro(val):
        1/0

    input_data = [1, 1, 1]
    coros = [coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop, return_exceptions=True)

    expected = _CacheInfo(
        hits=2,
        misses=1,
        maxsize=3,
        currsize=1,
    )

    assert coro.cache_info() == expected
    assert len(coro.cache) == 1
    assert len(coro.coros) == 0
    for item in ret:
        assert isinstance(item, ZeroDivisionError)

    one_more = coro(1)

    for fut in coros:
        assert fut is not one_more

    with pytest.raises(ZeroDivisionError):
        yield from one_more


@pytest.mark.run_loop
@asyncio.coroutine
def test_alru_cache_not_coroutine_exception(loop):
    @alru_cache(maxsize=3, loop=loop)
    def not_coro(val):
        1/0

    input_data = [1, 1, 1]
    coros = [not_coro(v) for v in input_data]

    ret = yield from asyncio.gather(*coros, loop=loop, return_exceptions=True)

    expected = _CacheInfo(
        hits=2,
        misses=1,
        maxsize=3,
        currsize=1,
    )

    assert not_coro.cache_info() == expected
    assert len(not_coro.cache) == 1
    assert len(not_coro.coros) == 0
    for item in ret:
        assert isinstance(item, ZeroDivisionError)

    one_more = not_coro(1)

    for fut in coros:
        assert fut is one_more

    with pytest.raises(ZeroDivisionError):
        yield from one_more
