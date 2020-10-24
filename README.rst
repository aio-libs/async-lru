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

This package is 100% port of Python built-in function `functools.lru_cache <https://docs.python.org/3/library/functools.html#functools.lru_cache>`_ for `asyncio <https://docs.python.org/3/library/asyncio.html>`_

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
        await get_pep.close()


    loop = asyncio.get_event_loop()

    loop.run_until_complete(main())

    loop.close()

Python 3.6+ is required

Thanks
------

The library was donated by `Ocean S.A. <https://ocean.io/>`_

Thanks to the company for contribution.
