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
    # Save current loop to restore after the test
    try:
        old_loop = asyncio.get_running_loop()
    except RuntimeError:
        old_loop = None
    new_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(new_loop)
    yield new_loop
    new_loop.close()
    if old_loop is not None:
        asyncio.set_event_loop(old_loop)


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
async def _cached_func(x):
    return x


def create_cached_func():
    return alru_cache(maxsize=128)(_cached_func)


async def _cached_func_ttl(x):
    return x


def create_cached_func_ttl():
    return alru_cache(maxsize=16, ttl=0.01)(_cached_func_ttl)


# Unbounded cache (no maxsize)
async def _cached_func_unbounded(x):
    return x


def create_cached_func_unbounded():
    return alru_cache()(_cached_func_unbounded)


async def _cached_func_unbounded_ttl(x):
    return x


def create_cached_func_unbounded_ttl():
    return alru_cache(ttl=0.01)(_cached_func_unbounded_ttl)


def create_cached_meth():
    class MethodsInstance:
        @alru_cache(maxsize=128)
        async def cached_meth(self, x):
            return x

    return MethodsInstance().cached_meth


def create_cached_meth_ttl():
    class MethodsInstance:
        @alru_cache(maxsize=16, ttl=0.01)
        async def cached_meth_ttl(self, x):
            return x

    return MethodsInstance().cached_meth_ttl


def create_cached_meth_unbounded():
    class MethodsInstance:
        @alru_cache()
        async def cached_meth_unbounded(self, x):
            return x

    return MethodsInstance().cached_meth_unbounded


def create_cached_meth_unbounded_ttl():
    class MethodsInstance:
        @alru_cache(ttl=0.01)
        async def cached_meth_unbounded_ttl(self, x):
            return x

    return MethodsInstance().cached_meth_unbounded_ttl


async def uncached_func(x):
    return x


funcs_no_ttl = [
    create_cached_func,
    create_cached_func_unbounded,
    create_cached_meth,
    create_cached_meth_unbounded,
]
no_ttl_ids = [
    "func-bounded",
    "func-unbounded",
    "meth-bounded",
    "meth-unbounded",
]

funcs_ttl = [
    create_cached_func_ttl,
    create_cached_func_unbounded_ttl,
    create_cached_meth_ttl,
    create_cached_meth_unbounded_ttl,
]
ttl_ids = [
    "func-bounded-ttl",
    "func-unbounded-ttl",
    "meth-bounded-ttl",
    "meth-unbounded-ttl",
]

all_funcs = [*funcs_no_ttl, *funcs_ttl]
all_ids = [*no_ttl_ids, *ttl_ids]


@pytest.mark.parametrize("factory", all_funcs, ids=all_ids)
def test_cache_hit_benchmark(
    benchmark: BenchmarkFixture,
    run_loop: Callable[..., Any],
    factory: Callable[[], _LRUCacheWrapper[Any]],
) -> None:
    func = factory()
    keys = list(range(10))
    for key in keys:
        run_loop(func, key)

    async def run() -> None:
        for _ in range(100):
            for key in keys:
                await func(key)

    benchmark(run_loop, run)


@pytest.mark.parametrize("factory", all_funcs, ids=all_ids)
def test_cache_miss_benchmark(
    benchmark: BenchmarkFixture,
    run_loop: Callable[..., Any],
    factory: Callable[[], _LRUCacheWrapper[Any]],
) -> None:
    func = factory()
    # Use 2048 objects (16x maxsize=128) to force evictions and measure actual misses
    unique_objects = [object() for _ in range(2048)]

    async def run() -> None:
        for obj in unique_objects:
            await func(obj)

    benchmark(run_loop, run)


@pytest.mark.parametrize("factory", all_funcs, ids=all_ids)
def test_cache_clear_benchmark(
    benchmark: BenchmarkFixture,
    run_loop: Callable[..., Any],
    factory: Callable[[], _LRUCacheWrapper[Any]],
) -> None:
    func = factory()
    for i in range(100):
        run_loop(func, i)

    benchmark(func.cache_clear)


@pytest.mark.parametrize("factory", funcs_ttl, ids=ttl_ids)
def test_cache_ttl_expiry_benchmark(
    benchmark: BenchmarkFixture,
    run_loop: Callable[..., Any],
    factory: Callable[[], _LRUCacheWrapper[Any]],
) -> None:
    func_ttl = factory()
    run_loop(func_ttl, 99)
    run_loop(asyncio.sleep, 0.02)

    benchmark(run_loop, func_ttl, 99)


@pytest.mark.parametrize("factory", all_funcs, ids=all_ids)
def test_cache_invalidate_benchmark(
    benchmark: BenchmarkFixture,
    run_loop: Callable[..., Any],
    factory: Callable[[], _LRUCacheWrapper[Any]],
) -> None:
    func = factory()
    keys = list(range(123, 321))
    for i in keys:
        run_loop(func, i)

    invalidate = func.cache_invalidate

    @benchmark
    def run() -> None:
        for i in keys:
            invalidate(i)


@pytest.mark.parametrize("factory", all_funcs, ids=all_ids)
def test_cache_info_benchmark(
    benchmark: BenchmarkFixture,
    run_loop: Callable[..., Any],
    factory: Callable[[], _LRUCacheWrapper[Any]],
) -> None:
    func = factory()
    keys = list(range(1000))
    for i in keys:
        run_loop(func, i)

    cache_info = func.cache_info

    @benchmark
    def run() -> None:
        for _ in keys:
            cache_info()


@pytest.mark.parametrize("factory", all_funcs, ids=all_ids)
def test_concurrent_cache_hit_benchmark(
    benchmark: BenchmarkFixture,
    run_loop: Callable[..., Any],
    factory: Callable[[], _LRUCacheWrapper[Any]],
) -> None:
    func = factory()
    keys = list(range(600, 700))
    for key in keys:
        run_loop(func, key)

    async def gather_coros():
        gather = asyncio.gather
        for _ in range(10):
            _ = await gather(*map(func, keys))

    benchmark(run_loop, gather_coros)


def test_cache_fill_eviction_benchmark(
    benchmark: BenchmarkFixture, run_loop: Callable[..., Any]
) -> None:
    func = create_cached_func()
    for i in range(-128, 0):
        run_loop(func, i)

    keys = list(range(5000))

    async def fill():
        for k in keys:
            await func(k)

    benchmark(run_loop, fill)


# ===========================
# Internal Microbenchmarks
# ===========================
# These benchmarks directly exercise internal (sync) methods and data structures
# not covered by the async public API benchmarks above.

# The relevant internal methods do not exist on _LRUCacheWrapperInstanceMethod,
# so we can skip methods for this part of the benchmark suite.
# We also skip wrappers with ttl because it raises KeyError.
only_funcs_no_ttl = funcs_no_ttl[:2]
func_ids_no_ttl = no_ttl_ids[:2]


@pytest.mark.parametrize("factory", only_funcs_no_ttl, ids=func_ids_no_ttl)
def test_internal_cache_hit_microbenchmark(
    benchmark: BenchmarkFixture,
    run_loop: Callable[..., Any],
    factory: Callable[[], _LRUCacheWrapper[Any]],
) -> None:
    """Directly benchmark _cache_hit (internal, sync) using parameterized funcs."""
    func = factory()
    cache_hit = func._cache_hit

    keys = list(range(128))
    for i in keys:
        run_loop(func, i)

    @benchmark
    def run() -> None:
        for i in keys:
            cache_hit(i)


@pytest.mark.parametrize("factory", only_funcs_no_ttl, ids=func_ids_no_ttl)
def test_internal_cache_miss_microbenchmark(
    benchmark: BenchmarkFixture, factory: Callable[[], _LRUCacheWrapper[Any]]
) -> None:
    """Directly benchmark _cache_miss (internal, sync) using parameterized funcs."""
    func = factory()
    cache_miss = func._cache_miss

    @benchmark
    def run() -> None:
        for i in range(128):
            cache_miss(i)


@pytest.mark.parametrize("factory", only_funcs_no_ttl, ids=func_ids_no_ttl)
@pytest.mark.parametrize("task_state", ["finished", "cancelled", "exception"])
def test_internal_task_done_callback_microbenchmark(
    benchmark: BenchmarkFixture,
    loop: asyncio.BaseEventLoop,
    factory: Callable[[], _LRUCacheWrapper[Any]],
    task_state: str,
) -> None:
    """Directly benchmark _task_done_callback (internal, sync) using parameterized funcs and task states."""
    func = factory()

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
