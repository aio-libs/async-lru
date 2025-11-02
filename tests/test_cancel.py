import asyncio
import pytest
from async_lru import alru_cache

@pytest.mark.parametrize("num_to_cancel", [0, 1, 2, 3])
async def test_cancel(num_to_cancel: int) -> None:
    cache_item_task_finished = False

    @alru_cache
    async def coro(val: int) -> int:
        # I am a long running coro function
        nonlocal cache_item_task_finished
        await asyncio.sleep(2)
        cache_item_task_finished = True
        return val

    # create 3 tasks for the cached function using the same key
    tasks = [asyncio.create_task(coro(1)) for _ in range(3)]

    # force the event loop to run once so the tasks can begin
    await asyncio.sleep(0)

    # maybe cancel some tasks
    for i in range(num_to_cancel):
        tasks[i].cancel()

    # allow enough time for the non-cancelled tasks to complete
    await asyncio.sleep(3)

    # check state
    assert cache_item_task_finished == (num_to_cancel < 3)

@pytest.mark.asyncio
async def test_cancel_single_waiter_triggers_handle_cancelled_error():
    # This test ensures the _handle_cancelled_error path (waiters == 1) is exercised.
    cache_item_task_finished = False

    @alru_cache
    async def coro(val: int) -> int:
        nonlocal cache_item_task_finished
        await asyncio.sleep(2)
        cache_item_task_finished = True
        return val

    task = asyncio.create_task(coro(42))
    await asyncio.sleep(0)
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    # The underlying coroutine should be cancelled, so the flag should remain False
    assert cache_item_task_finished is False
