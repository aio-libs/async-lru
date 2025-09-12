import asyncio
from typing import Callable

import pytest

from async_lru import alru_cache

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
    def run_the_loop(fn, *args, **kwargs):
        return loop.run_until_complete(_get_coro(fn(*args, **kwargs)))
    return run_the_loop


async def _get_coro(awaitable):
    """A helper function that turns an awaitable into a coroutine."""
    return await awaitable


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


async def uncached_func(x):
    return x


# Bounded cache benchmarks
def test_cache_hit_benchmark(benchmark: BenchmarkFixture, run_loop: Callable[..., Any]) -> None:
    run_loop(cached_func, 42)

    benchmark(run_loop, cached_func, 42)


def test_cache_miss_benchmark(benchmark: BenchmarkFixture, run_loop: Callable[..., Any]) -> None:
    benchmark(run_loop, cached_func, object())


def test_cache_fill_eviction_benchmark(benchmark: BenchmarkFixture, run_loop: Callable[..., Any]) -> None:
    keys = list(range(256))

    async def fill():
        for k in keys:
            await cached_func(k)

    benchmark(run_loop, fill)


def test_cache_clear_benchmark(benchmark: BenchmarkFixture, run_loop: Callable[..., Any]) -> None:    
    run_loop(cached_func, 1)

    benchmark(cached_func.cache_clear)


def test_cache_ttl_expiry_benchmark(benchmark: BenchmarkFixture, run_loop: Callable[..., Any]) -> None:
    run_loop(cached_func_ttl, 99)
    run_loop(asyncio.sleep, 0.02)

    benchmark(run_loop, cached_func_ttl, 99)


def test_cache_invalidate_benchmark(benchmark: BenchmarkFixture, run_loop: Callable[..., Any]) -> None:
    run_loop(cached_func, 123)

    benchmark(cached_func.cache_invalidate, 123)


def test_cache_info_benchmark(benchmark: BenchmarkFixture, run_loop: Callable[..., Any]) -> None:
    run_loop(cached_func, 1)

    benchmark(cached_func.cache_info)


def test_uncached_func_benchmark(benchmark: BenchmarkFixture, run_loop: Callable[..., Any]) -> None:
    benchmark(run_loop, uncached_func, 42)


def test_concurrent_cache_hit_benchmark(benchmark: BenchmarkFixture, run_loop: Callable[..., Any]) -> None:
    run_loop(cached_func, 77)

    benchmark(run_loop, asyncio.gather, *(cached_func(77) for _ in range(10)))


# Unbounded cache benchmarks
def test_cache_hit_unbounded_benchmark(benchmark: BenchmarkFixture, run_loop: Callable[..., Any]) -> None:
    run_loop(cached_func_unbounded, 42)

    benchmark(run_loop, cached_func_unbounded, 42)


def test_cache_miss_unbounded_benchmark(benchmark: BenchmarkFixture, run_loop: Callable[..., Any]) -> None:
    benchmark(run_loop, cached_func_unbounded, object())


def test_cache_clear_unbounded_benchmark(benchmark: BenchmarkFixture, run_loop: Callable[..., Any]) -> None:
    run_loop(cached_func_unbounded, 1)

    benchmark(cached_func_unbounded.cache_clear)


def test_cache_ttl_expiry_unbounded_benchmark(benchmark: BenchmarkFixture, run_loop: Callable[..., Any]) -> None:
    run_loop(cached_func_unbounded_ttl, 99)
    run_loop(asyncio.sleep, 0.02)

    benchmark(run_loop, cached_func_unbounded_ttl, 99)


def test_cache_invalidate_unbounded_benchmark(benchmark: BenchmarkFixture, run_loop: Callable[..., Any]) -> None:
    run_loop(cached_func_unbounded, 123)

    benchmark(cached_func_unbounded.cache_invalidate, 123)


def test_cache_info_unbounded_benchmark(benchmark: BenchmarkFixture, run_loop: Callable[..., Any]) -> None:
    run_loop(cached_func_unbounded, 1)

    benchmark(cached_func_unbounded.cache_info)


def test_concurrent_cache_hit_unbounded_benchmark(benchmark: BenchmarkFixture, run_loop: Callable[..., Any]) -> None:
    run_loop(cached_func_unbounded, 77)

    benchmark(run_loop, asyncio.gather, *(cached_func_unbounded(77) for _ in range(10)))
