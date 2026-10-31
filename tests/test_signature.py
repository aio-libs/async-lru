import inspect
from functools import partial

from async_lru import alru_cache


async def test_bound_method_signature() -> None:
    class Service:
        async def plain(self, value: int, *, enabled: bool = True) -> int:
            return value if enabled else 0

        cached = alru_cache(plain)

    service = Service()
    signature = inspect.signature(service.cached)
    assert signature == inspect.signature(service.plain)
    arguments = signature.bind(7, enabled=False)
    assert await service.cached(*arguments.args, **arguments.kwargs) == 0


async def test_bound_method_wrapped() -> None:
    class Service:
        @alru_cache
        async def cached(self, value: int) -> int:
            return value

    service = Service()
    assert await service.cached.__wrapped__(7) == 7
    assert service.cached.cache_info().currsize == 0


async def test_bound_partial_signature() -> None:
    class Service:
        async def plain(self, value: int, *, enabled: bool = True) -> int:
            return value if enabled else 0

        cached = alru_cache(partial(plain, enabled=False))

    service = Service()
    expected = inspect.signature(partial(service.plain, enabled=False))
    assert inspect.signature(service.cached) == expected
    assert await service.cached.__wrapped__(7) == 0
    assert await service.cached(7) == 0


async def test_classmethod_signature() -> None:
    class Service:
        @classmethod
        async def plain(cls, value: int) -> int:
            return value

        @classmethod
        @alru_cache
        async def cached(cls, value: int) -> int:
            return value

    assert inspect.signature(Service.cached) == inspect.signature(Service.plain)
    assert inspect.signature(Service().cached) == inspect.signature(Service().plain)
    assert await Service.cached(7) == 7


async def test_function_signature() -> None:
    async def plain(value: int, /, *, enabled: bool = True) -> int:
        return value if enabled else 0

    cached = alru_cache(plain)
    assert inspect.signature(cached) == inspect.signature(plain)
    assert cached.__wrapped__ is plain
    assert await cached(7) == 7
