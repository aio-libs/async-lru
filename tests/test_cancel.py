import asyncio

from async_lru import alru_cache


@pytest.mark.parametrize("num_to_cancel", [0, 1, 2, 3])
async def test_cancel(num_to_cancel: int) -> None:
    cache_item_task_finished = False
  
    @alru_cache
    async def coro(val: int) -> int:
        nonlocal cache_item_task_finished
        await asyncio.sleep(2)
        cache_item_task_finished = True
        return val

    tasks = [asyncio.create_task(coro()) for _ in range(3)]

    # force the event loop to run once so the tasks can begin
    await asyncio.sleep(0)

    for i in range(num_to_cancel):
        tasks[i].cancel()

    await asyncio.sleep(3)

    assert cache_item_task_finished is num_to_cancel < 3
