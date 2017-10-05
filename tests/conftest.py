import asyncio  # noqa # isort:skip
import gc

import pytest


asyncio.set_event_loop(None)


@pytest.fixture
def event_loop(request):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    yield loop

    loop.call_soon(loop.stop)
    loop.run_forever()
    loop.close()

    gc.collect()
    asyncio.set_event_loop(None)


@pytest.fixture
def loop(event_loop, request):
    return event_loop
