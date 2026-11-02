import inspect
from functools import partial

import pytest

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


@pytest.mark.parametrize("signature_on_wrapper", [False, True])
async def test_bound_method_explicit_signature(signature_on_wrapper: bool) -> None:
    class Service:
        async def plain(self, value: int, /, *, enabled: bool = True) -> int:
            return value if enabled else 0

        explicit_signature = inspect.signature(plain).replace(return_annotation=str)
        if not signature_on_wrapper:
            plain.__signature__ = explicit_signature  # type: ignore[attr-defined]
        cached = alru_cache(plain)
        if signature_on_wrapper:
            cached.__signature__ = explicit_signature  # type: ignore[attr-defined]

    service = Service()
    signature = inspect.signature(service.cached)
    assert signature == inspect.signature(service.plain).replace(return_annotation=str)
    assert inspect.signature(Service.__dict__["cached"]) == Service.explicit_signature
    arguments = signature.bind(7, enabled=False)
    assert await service.cached(*arguments.args, **arguments.kwargs) == 0
    assert inspect.signature(service.cached.__wrapped__) == inspect.signature(
        service.plain
    )


async def test_bound_method_variadic_explicit_signature() -> None:
    class Service:
        async def plain(*args: object) -> int:
            return len(args)

        plain.__signature__ = inspect.signature(plain)  # type: ignore[attr-defined]
        cached = alru_cache(plain)

    service = Service()
    signature = inspect.signature(service.cached)
    assert signature == inspect.signature(service.plain)
    arguments = signature.bind(7)
    assert await service.cached(*arguments.args, **arguments.kwargs) == 2


@pytest.mark.parametrize("signature_on_wrapper", [False, True])
@pytest.mark.parametrize(
    "explicit_signature",
    [
        inspect.Signature(),
        inspect.Signature([inspect.Parameter("value", inspect.Parameter.KEYWORD_ONLY)]),
        inspect.Signature([inspect.Parameter("kwargs", inspect.Parameter.VAR_KEYWORD)]),
    ],
    ids=["empty", "keyword-only", "variadic-keyword"],
)
async def test_bound_method_invalid_explicit_signature(
    explicit_signature: inspect.Signature, signature_on_wrapper: bool
) -> None:
    class Service:
        async def plain(self, value: int) -> int:
            return value

        if not signature_on_wrapper:
            plain.__signature__ = explicit_signature  # type: ignore[attr-defined]
        cached = alru_cache(plain)
        if signature_on_wrapper:
            cached.__signature__ = explicit_signature  # type: ignore[attr-defined]

    service = Service()
    cached = service.cached
    assert inspect.signature(cached) == explicit_signature
    assert cached.cache_info().currsize == 0
    assert await cached(value=7) == 7
    assert await service.cached(value=7) == 7
    assert service.cached.cache_info().hits == 1
    assert service.cached.cache_contains(value=7)
    assert await service.cached.__wrapped__(7) == 7
    service.cached.cache_clear()
    assert service.cached.cache_info().currsize == 0


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
