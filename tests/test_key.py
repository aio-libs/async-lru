import asyncio
from collections.abc import Callable

import pytest

from async_lru import alru_cache


async def test_key_excludes_argument(check_lru: Callable[..., None]) -> None:
    """Calls differing only in the excluded argument share one entry."""

    @alru_cache(key=lambda conn, query: query)
    async def query_db(conn: str, query: str) -> str:
        return f"{conn}={query}"

    assert await query_db("conn1", "SELECT 1") == "conn1=SELECT 1"
    check_lru(query_db, hits=0, misses=1, cache=1, tasks=0)

    assert await query_db("conn2", "SELECT 1") == "conn1=SELECT 1"
    check_lru(query_db, hits=1, misses=1, cache=1, tasks=0)

    assert await query_db("conn2", "SELECT 2") == "conn2=SELECT 2"
    check_lru(query_db, hits=1, misses=2, cache=2, tasks=0)


async def test_key_receives_kwargs(check_lru: Callable[..., None]) -> None:
    @alru_cache(key=lambda conn, *, query: query)
    async def query_db(conn: str, *, query: str) -> str:
        return f"{conn}={query}"

    assert await query_db("conn1", query="q") == "conn1=q"
    assert await query_db("conn2", query="q") == "conn1=q"
    check_lru(query_db, hits=1, misses=1, cache=1, tasks=0)


async def test_key_cache_invalidate(check_lru: Callable[..., None]) -> None:
    """cache_invalidate computes the same custom key as the call did."""

    @alru_cache(key=lambda conn, query: query)
    async def query_db(conn: str, query: str) -> str:
        return f"{conn}={query}"

    await query_db("conn1", "SELECT 1")
    check_lru(query_db, hits=0, misses=1, cache=1, tasks=0)

    # A different excluded argument still addresses the same entry.
    assert query_db.cache_invalidate("conn9", "SELECT 1")
    check_lru(query_db, hits=0, misses=1, cache=0, tasks=0)
    assert not query_db.cache_invalidate("conn9", "SELECT 1")


async def test_key_cache_contains(check_lru: Callable[..., None]) -> None:
    @alru_cache(key=lambda conn, query: query)
    async def query_db(conn: str, query: str) -> str:
        return f"{conn}={query}"

    await query_db("conn1", "SELECT 1")
    assert query_db.cache_contains("conn9", "SELECT 1")
    assert not query_db.cache_contains("conn9", "SELECT 2")


def test_key_with_typed_raises() -> None:
    with pytest.raises(ValueError, match="typed"):
        alru_cache(typed=True, key=lambda x: x)


def test_key_not_callable() -> None:
    with pytest.raises(TypeError, match="callable"):
        alru_cache(key="query")  # type: ignore[call-overload]


async def test_typed_without_key_still_works() -> None:
    @alru_cache(typed=True)
    async def coro(val: int) -> int:
        return val

    assert coro.cache_parameters()["typed"] is True
    assert await coro(1) == 1


async def test_key_on_method(check_lru: Callable[..., None]) -> None:
    """The key callable receives the instance for bound methods."""

    class Api:
        @alru_cache(key=lambda self, query: query)
        async def fetch(self, query: str) -> str:
            return f"{id(self)}={query}"

    first = Api()
    second = Api()
    result = await first.fetch("SELECT 1")
    # Another instance shares the entry since self is excluded.
    assert await second.fetch("SELECT 1") == result
    check_lru(Api.fetch, hits=1, misses=1, cache=1, tasks=0)


async def test_key_unhashable_result(check_lru: Callable[..., None]) -> None:
    @alru_cache(key=lambda val: [val])  # type: ignore[arg-type,return-value]
    async def coro(val: int) -> int:
        return val  # pragma: no cover  # the key fails before the call

    with pytest.raises(TypeError, match="unhashable"):
        await coro(1)
    check_lru(coro, hits=0, misses=0, cache=0, tasks=0)


async def test_key_callable_raising(check_lru: Callable[..., None]) -> None:
    def broken_key(val: int) -> int:
        raise RuntimeError("broken key")

    @alru_cache(key=broken_key)
    async def coro(val: int) -> int:
        return val  # pragma: no cover  # the key fails before the call

    with pytest.raises(RuntimeError, match="broken key"):
        await coro(1)
    check_lru(coro, hits=0, misses=0, cache=0, tasks=0)


async def test_key_with_ttl(check_lru: Callable[..., None]) -> None:
    @alru_cache(ttl=0.05, key=lambda conn, query: query)
    async def query_db(conn: str, query: str) -> str:
        return f"{conn}={query}"

    await query_db("conn1", "SELECT 1")
    assert await query_db("conn2", "SELECT 1") == "conn1=SELECT 1"
    check_lru(query_db, hits=1, misses=1, cache=1, tasks=0)

    await asyncio.sleep(0.06)
    assert await query_db("conn2", "SELECT 1") == "conn2=SELECT 1"
    check_lru(query_db, hits=1, misses=2, cache=1, tasks=0)


async def test_key_with_maxsize(check_lru: Callable[..., None]) -> None:
    @alru_cache(maxsize=1, key=lambda conn, query: query)
    async def query_db(conn: str, query: str) -> str:
        return f"{conn}={query}"

    await query_db("conn1", "SELECT 1")
    await query_db("conn1", "SELECT 2")
    check_lru(query_db, hits=0, misses=2, cache=1, tasks=0, maxsize=1)

    # The first entry was evicted; same query recomputes.
    assert await query_db("conn2", "SELECT 1") == "conn2=SELECT 1"
    check_lru(query_db, hits=0, misses=3, cache=1, tasks=0, maxsize=1)
