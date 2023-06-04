async_lru
=========

:info: Simple lru cache for asyncio

.. image:: https://travis-ci.com/aio-libs/async_lru.svg?branch=master
    :target: https://travis-ci.com/aio-libs/async_lru

.. image:: https://img.shields.io/pypi/v/async_lru.svg
    :target: https://pypi.python.org/pypi/async_lru

.. image:: https://codecov.io/gh/aio-libs/async_lru/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/aio-libs/async_lru

Installation
------------

.. code-block:: shell

    pip install async_lru

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


TTL (time-to-live, expiration on timeout) is supported by accepting `ttl` configuration
parameter (off by default):

.. code-block:: python

    @alru_cache(ttl=5)
    async def func(arg):
        return arg * 2


The library supports explicit invalidation for specific function call by
`cache_invalidate()`:

.. code-block:: python

    @alru_cache(ttl=5)
    async def func(arg1, arg2):
        return arg1 + arg2

    func.cache_invalidate(1, arg2=2)

The method returns `True` if corresponding arguments set was cached already, `False`
otherwise.


Python 3.8+ is required

Thanks
------

The library was donated by `Ocean S.A. <https://ocean.io/>`_

Thanks to the company for contribution.
