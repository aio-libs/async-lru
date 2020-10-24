import pytest

from async_lru import alru_cache


pytestmark = pytest.mark.asyncio


async def test_alru_cache_open(check_lru, loop):
    @alru_cache(loop=loop)
    async def coro(val):
        return val

    await coro(1)

    check_lru(coro, hits=0, misses=1, cache=1, tasks=0)

    with pytest.raises(RuntimeError):
        coro.open()

    close = coro.close(loop=loop)

    assert coro.closed

    with pytest.raises(RuntimeError):
        await coro()

    with pytest.raises(RuntimeError):
        coro.open()

    await close

    check_lru(coro, hits=0, misses=0, cache=0, tasks=0)

    coro.open()

    ret = await coro(1)

    assert ret == 1

    check_lru(coro, hits=0, misses=1, cache=1, tasks=0)
