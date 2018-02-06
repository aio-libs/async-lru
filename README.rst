async_lru
=========

:info: Simple lru cache for asyncio

.. image:: https://travis-ci.org/aio-libs/async_lru.svg?branch=master
    :target: https://travis-ci.org/aio-libs/async_lru

.. image:: https://img.shields.io/pypi/v/async_lru.svg
    :target: https://pypi.python.org/pypi/async_lru

.. image:: https://codecov.io/gh/aio-libs/async_lru/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/aio-libs/async_lru

:info: Simple lru cache for asyncio

Asynchronous "Least Recently Used"-style cache for input/output use.
For example, using async-lru with resources available via HTTP allows for
those resources to be downloaded, cached and returned when remote HTTP
resources are actually available. async-lru helps programmers build a higher
level view of these network calls for APIs to be built on.

See example below:

Installation
------------

.. code-block:: shell

    pip install async_lru

Usage
-----

Below: the webpage at "https://www.python.org/" is downloaded (via HTTP) and stored 6 times.
It is both run once, as a proof that you can control how many times a resource or set of resources are requested, or as many times as needed within a loop using run_until_complete()  

.. code-block:: python

    import asyncio

    import aiohttp
    from async_lru import alru_cache

    calls = 0

    @alru_cache()
    async def download(url):
        global calls

        calls += 1

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return await response.text()


    async def main():
        coros = [
            download('https://www.python.org/'),
            download('https://www.python.org/'),
            download('https://www.python.org/'),
            download('https://www.python.org/'),
            download('https://www.python.org/'),
            download('https://www.python.org/'),
        ]

        await asyncio.gather(*coros)

        assert calls == 1


    loop = asyncio.get_event_loop()

    loop.run_until_complete(main())

    # closing is optional, but strictly recommended
    loop.run_until_complete(download.close())

    loop.close()

Python 3.3+ is required

Thanks
------

The library was donated by `Ocean S.A. <https://ocean.io/>`_

Thanks to the company for contribution.
