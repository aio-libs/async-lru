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
    for index, input in enumerate(inputs):
        expected_traceback_length = 3 if index == 0 else 2
        try:
            await coro(input)
        except ZeroDivisionError as err:
            traceback_length = len(traceback.extract_tb(err.__traceback__))
            assert traceback_length == expected_traceback_length
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
        expected_traceback_length = 3
        expected_exc_local = index > 0
        try:
            await coro(input)
        except ZeroDivisionError as err:
            stack_summary = traceback.StackSummary.extract(
                traceback.walk_tb(err.__traceback__), capture_locals=True
            )
            assert len(stack_summary) == expected_traceback_length
            exc_local_seen = False
            for frame in stack_summary:
                if 'exc' in frame.locals:
                    exc_local_seen = True
                    assert frame.locals['exc'] == 'None'
            assert expected_exc_local == False or exc_local_seen == True
        else:
            assert 0

    check_lru(coro, hits=0, misses=3, cache=1, tasks=0)

    with pytest.raises(ZeroDivisionError):
        await coro(1)

    check_lru(coro, hits=0, misses=4, cache=1, tasks=0)
