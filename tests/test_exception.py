import asyncio
import gc
import sys
from typing import Callable

import pytest

from async_lru import alru_cache


async def test_alru_exception(check_lru: Callable[..., None]) -> None:
    @alru_cache()
    async def coro(val: int) -> None:
        1 / 0

    inputs = [1, 1, 1]
    coros = [coro(v) for v in inputs]

    ret = await asyncio.gather(*coros, return_exceptions=True)

    check_lru(coro, hits=2, misses=1, cache=0, tasks=0)

    for item in ret:
        assert isinstance(item, ZeroDivisionError)

    with pytest.raises(ZeroDivisionError):
        await coro(1)

    check_lru(coro, hits=2, misses=2, cache=0, tasks=0)


@pytest.mark.xfail(
    reason="Memory leak is not fixed for PyPy3.9",
    condition=sys.implementation.name == "pypy",
)
async def test_alru_exception_reference_cleanup(check_lru: Callable[..., None]) -> None:
    class CustomClass:
        ...

    @alru_cache()
    async def coro(val: int) -> None:
        _ = CustomClass()  # object we are verifying not to leak
        1 / 0

    coros = [coro(v) for v in range(1000)]

    await asyncio.gather(*coros, return_exceptions=True)

    check_lru(coro, hits=0, misses=1000, cache=0, tasks=0)

    await asyncio.sleep(0.00001)
    gc.collect()

    assert (
        len([obj for obj in gc.get_objects() if isinstance(obj, CustomClass)]) == 0
    ), "Only objects in the cache should be left in memory."
