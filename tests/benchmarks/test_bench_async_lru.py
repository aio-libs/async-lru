import asyncio
import pytest
from async_lru import alru_cache

pytestmark = pytest.mark.benchmark

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
@pytest.mark.asyncio
async def test_cache_hit_benchmark(benchmark):
    await cached_func(42)
    async def hit():
        await cached_func(42)
    await benchmark.asyncio(hit)

async def test_cache_miss_benchmark(benchmark):
    async def miss():
        await cached_func(object())
    await benchmark.asyncio(miss)

async def test_cache_fill_eviction_benchmark(benchmark):
    keys = list(range(256))
    async def fill():
        for k in keys:
            await cached_func(k)
    await benchmark.asyncio(fill)

async def test_cache_clear_benchmark(benchmark):
    await cached_func(1)
    async def clear():
        await cached_func.cache_clear()
    await benchmark.asyncio(clear)

async def test_cache_ttl_expiry_benchmark(benchmark):
    await cached_func_ttl(99)
    await asyncio.sleep(0.02)
    async def ttl_expire():
        await cached_func_ttl(99)
    await benchmark.asyncio(ttl_expire)

async def test_cache_invalidate_benchmark(benchmark):
    await cached_func(123)
    async def invalidate():
        await cached_func.cache_invalidate(123)
    await benchmark.asyncio(invalidate)

async def test_cache_info_benchmark(benchmark):
    await cached_func(1)
    async def info():
        cached_func.cache_info()
    await benchmark.asyncio(info)

async def test_uncached_func_benchmark(benchmark):
    async def raw():
        await uncached_func(42)
    await benchmark.asyncio(raw)

async def test_concurrent_cache_hit_benchmark(benchmark):
    await cached_func(77)
    async def concurrent_hit():
        await asyncio.gather(*(cached_func(77) for _ in range(10)))
    await benchmark.asyncio(concurrent_hit)

# Unbounded cache benchmarks
async def test_cache_hit_unbounded_benchmark(benchmark):
    await cached_func_unbounded(42)
    async def hit():
        await cached_func_unbounded(42)
    await benchmark.asyncio(hit)

async def test_cache_miss_unbounded_benchmark(benchmark):
    async def miss():
        await cached_func_unbounded(object())
    await benchmark.asyncio(miss)

async def test_cache_clear_unbounded_benchmark(benchmark):
    await cached_func_unbounded(1)
    async def clear():
        await cached_func_unbounded.cache_clear()
    await benchmark.asyncio(clear)

async def test_cache_ttl_expiry_unbounded_benchmark(benchmark):
    await cached_func_unbounded_ttl(99)
    await asyncio.sleep(0.02)
    async def ttl_expire():
        await cached_func_unbounded_ttl(99)
    await benchmark.asyncio(ttl_expire)

async def test_cache_invalidate_unbounded_benchmark(benchmark):
    await cached_func_unbounded(123)
    async def invalidate():
        await cached_func_unbounded.cache_invalidate(123)
    await benchmark.asyncio(invalidate)

async def test_cache_info_unbounded_benchmark(benchmark):
    await cached_func_unbounded(1)
    async def info():
        cached_func_unbounded.cache_info()
    await benchmark.asyncio(info)

async def test_concurrent_cache_hit_unbounded_benchmark(benchmark):
    await cached_func_unbounded(77)
    async def concurrent_hit():
        await asyncio.gather(*(cached_func_unbounded(77) for _ in range(10)))
    await benchmark.asyncio(concurrent_hit)
