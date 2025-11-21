import asyncio
from functools import partial
from typing import Any, Callable

import pytest

from async_lru import _LRUCacheWrapper, alru_cache


try:
    from pytest_codspeed import BenchmarkFixture
except ImportError:  # pragma: no branch  # only hit in cibuildwheel
    pytestmark = pytest.mark.skip("pytest-codspeed needs to be installed")
else:
    pytestmark = pytest.mark.benchmark


@pytest.fixture
def loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture
def run_loop(loop):
    async def _get_coro(awaitable):
        """A helper function that turns an awaitable into a coroutine."""
        return await awaitable

    def run_the_loop(fn, *args, **kwargs):
        awaitable = fn(*args, **kwargs)
        coro = awaitable if asyncio.iscoroutine(awaitable) else _get_coro(awaitable)
        return loop.run_until_complete(coro)

    return run_the_loop


# Bounded cache (LRU)
@alru_cache(maxsize=128)
async def cached_func(x):
    return x


@alru_cache(maxsize=16, ttl=0.01)
async def cached_func_ttl(x):
    return x


# Unbounded cache (no maxsize)
@alru_cache()
async def cached_func_unbounded(x):
    return x


@alru_cache(ttl=0.01)
async def cached_func_unbounded_ttl(x):
    return x


class Methods:
    @alru_cache(maxsize=128)
    async def cached_meth(self, x):
        return x

    @alru_cache(maxsize=16, ttl=0.01)
    async def cached_meth_ttl(self, x):
        return x

    @alru_cache()
    async def cached_meth_unbounded(self, x):
        return x

    @alru_cache(ttl=0.01)
    async def cached_meth_unbounded_ttl(self, x):
        return x


async def uncached_func(x):
    return x


funcs_no_ttl = [
    cached_func,
    cached_func_unbounded,
    Methods.cached_meth,
    Methods.cached_meth_unbounded,
]
no_ttl_ids = [
    "func-bounded",
    "func-unbounded",
    "meth-bounded",
    "meth-unbounded",
]

funcs_ttl = [
    cached_func_ttl,
    cached_func_unbounded_ttl,
    Methods.cached_meth_ttl,
    Methods.cached_meth_unbounded_ttl,
]
ttl_ids = [
    "func-bounded-ttl",
    "func-unbounded-ttl",
    "meth-bounded-ttl",
    "meth-unbounded-ttl",
]

all_funcs = [*funcs_no_ttl, *funcs_ttl]
all_ids = [*no_ttl_ids, *ttl_ids]


@pytest.mark.parametrize("func", all_funcs, ids=all_ids)
def test_cache_hit_benchmark(
    benchmark: BenchmarkFixture,
    run_loop: Callable[..., Any],
    func: _LRUCacheWrapper[Any],
) -> None:
    # Populate cache
    keys = list(range(10))
    for key in keys:
        run_loop(func, key)

    async def run() -> None:
        for _ in range(100):
            for key in keys:
                await func(key)

    benchmark(run_loop, run)


@pytest.mark.parametrize("func", all_funcs, ids=all_ids)
def test_cache_miss_benchmark(
    benchmark: BenchmarkFixture,
    run_loop: Callable[..., Any],
    func: _LRUCacheWrapper[Any],
) -> None:
    unique_objects = [object() for _ in range(128)]
    func.cache_clear()

    async def run() -> None:
        for obj in unique_objects:
            await func(obj)

    benchmark(run_loop, run)


@pytest.mark.parametrize("func", all_funcs, ids=all_ids)
def test_cache_clear_benchmark(
    benchmark: BenchmarkFixture,
    run_loop: Callable[..., Any],
    func: _LRUCacheWrapper[Any],
) -> None:
    for i in range(100):
        run_loop(func, i)

    benchmark(func.cache_clear)


@pytest.mark.parametrize("func_ttl", funcs_ttl, ids=ttl_ids)
def test_cache_ttl_expiry_benchmark(
    benchmark: BenchmarkFixture,
    run_loop: Callable[..., Any],
    func_ttl: _LRUCacheWrapper[Any],
) -> None:
    run_loop(func_ttl, 99)
    run_loop(asyncio.sleep, 0.02)

    benchmark(run_loop, func_ttl, 99)


@pytest.mark.parametrize("func", all_funcs, ids=all_ids)
def test_cache_invalidate_benchmark(
    benchmark: BenchmarkFixture,
    run_loop: Callable[..., Any],
    func: _LRUCacheWrapper[Any],
) -> None:
    # Populate cache
    keys = list(range(123, 321))
    for i in keys:
        run_loop(func, i)

    invalidate = func.cache_invalidate

    @benchmark
    def run() -> None:
        for i in keys:
            invalidate(i)


@pytest.mark.parametrize("func", all_funcs, ids=all_ids)
def test_cache_info_benchmark(
    benchmark: BenchmarkFixture,
    run_loop: Callable[..., Any],
    func: _LRUCacheWrapper[Any],
) -> None:
    # Populate cache
    keys = list(range(1000))
    for i in keys:
        run_loop(func, i)

    cache_info = func.cache_info

    @benchmark
    def run() -> None:
        for _ in keys:
            cache_info()


@pytest.mark.parametrize("func", all_funcs, ids=all_ids)
def test_concurrent_cache_hit_benchmark(
    benchmark: BenchmarkFixture,
    run_loop: Callable[..., Any],
    func: _LRUCacheWrapper[Any],
) -> None:
    # Populate cache
    keys = list(range(600, 700))
    for key in keys:
        run_loop(func, key)

    async def gather_coros():
        gather = asyncio.gather
        for _ in range(10):
            return await gather(*map(func, keys))

    benchmark(run_loop, gather_coros)


def test_cache_fill_eviction_benchmark(
    benchmark: BenchmarkFixture, run_loop: Callable[..., Any]
) -> None:
    # Populate cache
    for i in range(-128, 0):
        run_loop(cached_func, i)

    keys = list(range(5000))

    async def fill():
        for k in keys:
            await cached_func(k)

    benchmark(run_loop, fill)


# ===========================
# Internal Microbenchmarks
# ===========================
# These benchmarks directly exercise internal (sync) methods and data structures
# not covered by the async public API benchmarks above.

# The relevant internal methods do not exist on _LRUCacheWrapperInstanceMethod,
# so we can skip methods for this part of the benchmark suite.
# We also skip wrappers with ttl because it raises KeyError.
only_funcs_no_ttl = all_funcs[:2]
func_ids_no_ttl = all_ids[:2]


@pytest.mark.parametrize("func", only_funcs_no_ttl, ids=func_ids_no_ttl)
def test_internal_cache_hit_microbenchmark(
    benchmark: BenchmarkFixture,
    run_loop: Callable[..., Any],
    func: _LRUCacheWrapper[Any],
) -> None:
    """Directly benchmark _cache_hit (internal, sync) using parameterized funcs."""
    cache_hit = func._cache_hit

    # Populate cache
    keys = list(range(128))
    for i in keys:
        run_loop(func, i)

    @benchmark
    def run() -> None:
        for i in keys:
            cache_hit(i)


@pytest.mark.parametrize("func", only_funcs_no_ttl, ids=func_ids_no_ttl)
def test_internal_cache_miss_microbenchmark(
    benchmark: BenchmarkFixture, func: _LRUCacheWrapper[Any]
) -> None:
    """Directly benchmark _cache_miss (internal, sync) using parameterized funcs."""
    cache_miss = func._cache_miss

    @benchmark
    def run() -> None:
        for i in range(128):
            cache_miss(i)


@pytest.mark.parametrize("func", only_funcs_no_ttl, ids=func_ids_no_ttl)
@pytest.mark.parametrize("task_state", ["finished", "cancelled", "exception"])
def test_internal_task_done_callback_microbenchmark(
    benchmark: BenchmarkFixture,
    loop: asyncio.BaseEventLoop,
    func: _LRUCacheWrapper[Any],
    task_state: str,
) -> None:
    """Directly benchmark _task_done_callback (internal, sync) using parameterized funcs and task states."""

    # Create a dummy coroutine and task
    async def dummy_coro():
        if task_state == "exception":
            raise ValueError("test exception")
        return 123

    task = loop.create_task(dummy_coro())
    if task_state == "finished":
        loop.run_until_complete(task)
    elif task_state == "cancelled":
        task.cancel()
        try:
            loop.run_until_complete(task)
        except asyncio.CancelledError:
            pass
    elif task_state == "exception":
        try:
            loop.run_until_complete(task)
        except Exception:
            pass

    iterations = range(1000)
    callback_fn = func._task_done_callback

    @benchmark
    def run() -> None:
        for i in iterations:
            callback = partial(callback_fn, i)
            callback(task)
