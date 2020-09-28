import asyncio
import traceback

import pytest

from async_lru import alru_cache

pytestmark = pytest.mark.asyncio


async def test_alru_cache_exception(check_lru, loop):
    @alru_cache(cache_exceptions=True, loop=loop)
    async def coro(val):
        1/0

    inputs = [1, 1, 1]
    prev_traceback_length = 0
    for input in inputs:
        try:
            await coro(input)
        except ZeroDivisionError as err:
            traceback_length = len(traceback.extract_tb(err.__traceback__))
            if prev_traceback_length > 0:
                assert traceback_length <= prev_traceback_length
            prev_traceback_length = traceback_length
        else:
            assert 0

    check_lru(coro, hits=2, misses=1, cache=1, tasks=0)

    with pytest.raises(ZeroDivisionError):
        await coro(1)

    check_lru(coro, hits=3, misses=1, cache=1, tasks=0)


async def test_alru_not_cache_exception(check_lru, loop):
    @alru_cache(cache_exceptions=False, loop=loop)
    async def coro(val):
        1/0

    inputs = [1, 1, 1]
    for index, input in enumerate(inputs):
        try:
            await coro(input)
        except ZeroDivisionError as err:
            if index > 0:
                # find the stack frame of the wrapper that references the
                # previous exception object and verify that it is released
                stack_summary = traceback.StackSummary.extract(
                    traceback.walk_tb(err.__traceback__), capture_locals=True
                )
                for frame in stack_summary:
                    if (frame.filename.endswith('/async_lru.py') and
                            frame.name == 'wrapped'):
                        assert 'exc' in frame.locals
                        assert frame.locals['exc'] == 'None'
                        break
        else:
            assert 0

    check_lru(coro, hits=0, misses=3, cache=1, tasks=0)

    with pytest.raises(ZeroDivisionError):
        await coro(1)

    check_lru(coro, hits=0, misses=4, cache=1, tasks=0)


@pytest.mark.xfail
async def test_alru_not_cache_exception_edge_case(check_lru, loop):
    @alru_cache(cache_exceptions=False, loop=loop)
    async def coro(val):
        1/0

    inputs = [1, 1, 1]
    coros = [coro(v) for v in inputs]

    # process all coroutines to trigger edge case of returned cached
    # exceptions even when cache_exceptions is False
    await asyncio.gather(*coros, loop=loop, return_exceptions=True)

    # hits should be 0 for this case
    check_lru(coro, hits=0, misses=3, cache=1, tasks=0)
