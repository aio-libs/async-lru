import asyncio
import gc
import os

import pytest

asyncio.set_event_loop(None)


@pytest.fixture
def event_loop(request):
    asyncio.set_event_loop(None)
    loop = asyncio.new_event_loop()
    loop.set_debug(bool(os.environ.get('PYTHONASYNCIODEBUG')))

    request.addfinalizer(lambda: asyncio.set_event_loop(None))

    yield loop

    loop.call_soon(loop.stop)
    loop.run_forever()
    loop.close()

    gc.collect()


@pytest.fixture
def loop(event_loop, request):
    return event_loop
