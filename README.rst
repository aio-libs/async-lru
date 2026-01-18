async-lru
=========

:info: Simple lru cache for asyncio

.. image:: https://github.com/aio-libs/async-lru/actions/workflows/ci-cd.yml/badge.svg?event=push
   :target: https://github.com/aio-libs/async-lru/actions/workflows/ci-cd.yml?query=event:push
   :alt: GitHub Actions CI/CD workflows status

.. image:: https://img.shields.io/pypi/v/async-lru.svg?logo=Python&logoColor=white
   :target: https://pypi.org/project/async-lru
   :alt: async-lru @ PyPI

.. image:: https://codecov.io/gh/aio-libs/async-lru/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/aio-libs/async-lru

.. image:: https://img.shields.io/matrix/aio-libs:matrix.org?label=Discuss%20on%20Matrix%20at%20%23aio-libs%3Amatrix.org&logo=matrix&server_fqdn=matrix.org&style=flat
   :target: https://matrix.to/#/%23aio-libs:matrix.org
   :alt: Matrix Room — #aio-libs:matrix.org

.. image:: https://img.shields.io/matrix/aio-libs-space:matrix.org?label=Discuss%20on%20Matrix%20at%20%23aio-libs-space%3Amatrix.org&logo=matrix&server_fqdn=matrix.org&style=flat
   :target: https://matrix.to/#/%23aio-libs-space:matrix.org
   :alt: Matrix Space — #aio-libs-space:matrix.org

Installation
------------

.. code-block:: shell

    pip install async-lru

Usage
-----

This package is a port of Python's built-in `functools.lru_cache <https://docs.python.org/3/library/functools.html#functools.lru_cache>`_ function for `asyncio <https://docs.python.org/3/library/asyncio.html>`_. To better handle async behaviour, it also ensures multiple concurrent calls will only result in 1 call to the wrapped function, with all ``await``\s receiving the result of that call when it completes.

.. code-block:: python

    import asyncio

    import aiohttp
    from async_lru import alru_cache


    @alru_cache(maxsize=32)
    async def get_pep(num):
        resource = 'http://www.python.org/dev/peps/pep-%04d/' % num
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(resource) as s:
                    return await s.read()
            except aiohttp.ClientError:
                return 'Not Found'


    async def main():
        for n in 8, 290, 308, 320, 8, 218, 320, 279, 289, 320, 9991:
            pep = await get_pep(n)
            print(n, len(pep))

        print(get_pep.cache_info())
        # CacheInfo(hits=3, misses=8, maxsize=32, currsize=8)

        # closing is optional, but highly recommended
        await get_pep.cache_close()


    asyncio.run(main())


TTL (time-to-live in seconds, expiration on timeout) is supported by accepting `ttl` configuration
parameter (off by default):

.. code-block:: python

    @alru_cache(ttl=5)
    async def func(arg):
        return arg * 2

To prevent thundering herd issues when many cache entries expire simultaneously,
you can add ``jitter`` to randomize the TTL for each entry:

.. code-block:: python

    @alru_cache(ttl=3600, jitter=1800)
    async def func(arg):
        return arg * 2

With ``ttl=3600, jitter=1800``, each cache entry will have a random TTL
between 3600 and 5400 seconds, spreading out invalidations over time.


The library supports explicit invalidation for specific function call by
`cache_invalidate()`:

.. code-block:: python

    @alru_cache(ttl=5)
    async def func(arg1, arg2):
        return arg1 + arg2

    func.cache_invalidate(1, arg2=2)

The method returns `True` if corresponding arguments set was cached already, `False`
otherwise.

Limitations
-----------

**Thread Safety**: ``alru_cache`` is **not thread-safe** when the same cached function instance
is called from multiple event loops running on different threads. The cache uses an unsynchronized
``OrderedDict`` which can lead to race conditions.

For typical asyncio applications using a single event loop, this is not a concern. If your
application runs multiple event loops on different threads, you have these options:

**Option 1: Per-thread caching** - Each thread gets its own cache instance (recommended):

.. code-block:: python

    # Example: Per-thread caching using threading.local()
    import threading

    _local = threading.local()

    def get_cached_fetcher():
        if not hasattr(_local, 'fetcher'):
            @alru_cache(maxsize=100)
            async def fetch_data(key):
                # ... implementation
                pass
            _local.fetcher = fetch_data
        return _local.fetcher

    # Usage: each thread gets its own cache instance
    async def worker():
        fetcher = get_cached_fetcher()
        result = await fetcher("some_key")
        return result

**Option 2: External synchronization** - Use ``threading.Lock`` around all cache operations
(impacts performance).

**Option 3: Single-threaded design** - Keep cached functions within a single event loop
(simplest if feasible).

See issue `#611 <https://github.com/aio-libs/async-lru/issues/611>`_ for more details.

Benchmarks
----------

async-lru uses `CodSpeed <https://codspeed.io/>`_ for performance regression testing.

To run the benchmarks locally:

.. code-block:: shell

    pip install -r requirements-dev.txt
    pytest --codspeed benchmark.py

The benchmark suite covers both bounded (with maxsize) and unbounded (no maxsize) cache configurations. Scenarios include:

- Cache hit
- Cache miss
- Cache fill/eviction (cycling through more keys than maxsize)
- Cache clear
- TTL expiry
- Cache invalidation
- Cache info retrieval
- Concurrent cache hits
- Baseline (uncached async function)

On CI, benchmarks are run automatically via GitHub Actions on Python 3.13, and results are uploaded to CodSpeed (if a `CODSPEED_TOKEN` is configured). You can view performance history and detect regressions on the CodSpeed dashboard.

Thanks
------

The library was donated by `Ocean S.A. <https://ocean.io/>`_

Thanks to the company for contribution.
