async_lru
=========

:info: Simple lru cache for asyncio

.. image:: https://img.shields.io/travis/wikibusiness/async_lru.svg
    :target: https://travis-ci.org/wikibusiness/async_lru

.. image:: https://img.shields.io/pypi/v/async_lru.svg
    :target: https://pypi.python.org/pypi/async_lru

Installation
------------

.. code-block:: shell

    pip install async_lru

Usage
-----

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
