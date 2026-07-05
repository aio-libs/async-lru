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

To check whether a specific set of arguments is present in the cache without
affecting hit/miss counters or LRU ordering, use `cache_contains()`:

.. code-block:: python

    @alru_cache(maxsize=32)
    async def func(arg1, arg2):
        return arg1 + arg2

    await func(1, arg2=2)

    func.cache_contains(1, arg2=2)  # True
    func.cache_contains(3, arg2=4)  # False

The method returns `True` if the result for the given arguments is cached, `False`
otherwise.

Custom cache keys
-----------------

By default the cache key is built from all arguments, like
``functools.lru_cache`` does. The ``key`` parameter accepts a callable that
receives the same arguments as the wrapped function and returns the cache key,
so arguments that do not affect the result can be excluded from it. This is an
async-lru extension beyond the ``functools.lru_cache`` interface:

.. code-block:: python

    @alru_cache(key=lambda db, query: query)
    async def query_db(db, query):
        return await db.execute(query)

    # Both calls share one cache entry despite the different connections.
    await query_db(conn1, "SELECT ...")
    await query_db(conn2, "SELECT ...")

The returned key must be hashable. ``cache_invalidate()`` and
``cache_contains()`` compute the key the same way, so they accept the full
argument list as usual. For decorated methods the key callable receives the
instance as its first argument. Passing ``typed=True`` together with ``key``
raises ``ValueError``, since ``typed`` only affects the default key
computation.

Limitations
-----------

**Event Loop Affinity**: ``alru_cache`` enforces that a cache instance is used with only
one event loop. If you attempt to use a cached function from a different event loop than
where it was first called, a ``RuntimeError`` will be raised:

.. code-block:: text

    RuntimeError: alru_cache is not safe to use across event loops: this cache
    instance was first used with a different event loop.
    Use separate cache instances per event loop.

For typical asyncio applications using a single event loop, this is automatic and requires
no configuration. If your application uses multiple event loops, create separate cache
instances per loop:

.. code-block:: python

    import threading

    _local = threading.local()

    def get_cached_fetcher():
        if not hasattr(_local, 'fetcher'):
            @alru_cache(maxsize=100)
            async def fetch_data(key):
                ...
            _local.fetcher = fetch_data
        return _local.fetcher

You can also reuse the logic of an already decorated function in a new loop by accessing ``__wrapped__``:

.. code-block:: python

    @alru_cache(maxsize=32)
    async def my_task(x):
        ...

    # In Loop 1:
    # my_task() uses the default global cache instance

    # In Loop 2 (or a new thread):
    # Create a fresh cache instance for the same logic
    cached_task_loop2 = alru_cache(maxsize=32)(my_task.__wrapped__)
    await cached_task_loop2(x)

Security considerations
-----------------------

**Cache keys are built only from explicit arguments.** Like
`functools.lru_cache <https://docs.python.org/3/library/functools.html#functools.lru_cache>`_,
``alru_cache`` derives its cache key solely from the positional and keyword arguments
passed to the wrapped function. Implicit, request-scoped context — such as
authentication headers, the current user or tenant, ``contextvars``, thread/task
locals, or module globals — is **not** part of the key and therefore **not** isolated
between callers.

Because concurrent calls with the same key also share a single in-flight result (see
the Usage section above), a value computed for one caller can be returned to another whenever
their arguments are equal. In multi-tenant or multi-user services this can lead to
cross-tenant data exposure if the cached coroutine's result depends on anything other
than its explicit arguments.

To use ``alru_cache`` safely in these contexts:

- **Make the cached coroutine a pure function of its arguments.** Any value that
  affects the result — ``user_id``, ``tenant_id``, role, locale, feature flags, etc. —
  must be passed as an argument so it becomes part of the cache key, or use a separate
  cache instance per security domain.
- **Avoid caching context-dependent functions.** If a function reads request-scoped
  state from ``contextvars``/globals rather than from its arguments, either refactor it
  to take that state explicitly or do not cache it.
- **Consider** ``typed=True`` **when callers may pass multiple types.** With the default
  ``typed=False``, arguments that compare and hash equal share an entry (for example
  ``1`` and ``1.0``, or ``True`` and ``1``). Pass ``typed=True`` to key such arguments
  distinctly.
- **Be wary of attacker-controlled key arguments.** Objects with unusual ``__hash__`` /
  ``__eq__`` semantics can collide unexpectedly; only use trusted, well-behaved values
  as cache key components.

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
