"""Tests for PEP 649 deferred annotations (Python 3.14+).

On Python 3.14 annotations are evaluated lazily via ``__annotate__``.
Copying ``fn.__annotations__`` eagerly at decoration time forces that
evaluation and crashes with ``NameError`` when the annotation refers to
a name defined after the decorated function, a pattern that works with
``functools.lru_cache``.
"""

import inspect
import sys
from functools import lru_cache

import pytest

from async_lru import alru_cache


py314 = pytest.mark.skipif(
    sys.version_info < (3, 14),
    reason="deferred annotation evaluation requires Python 3.14",
)


@py314
async def test_deco_with_annotation_defined_after() -> None:
    @alru_cache(maxsize=1)
    async def get_foo() -> Foo:
        return Foo()

    class Foo:
        pass

    first = await get_foo()
    assert isinstance(first, Foo)
    assert await get_foo() is first


@py314
async def test_annotations_stay_lazy_like_lru_cache() -> None:
    @alru_cache(maxsize=1)
    async def get_foo_async() -> Foo:
        return Foo()

    @lru_cache(maxsize=1)
    def get_foo_sync() -> Foo:
        return Foo()

    class Foo:
        pass

    assert (
        inspect.get_annotations(get_foo_async)
        == inspect.get_annotations(get_foo_sync)
        == {"return": Foo}
    )


@py314
async def test_unresolvable_annotation_raises_only_on_access() -> None:
    @alru_cache(maxsize=1)
    async def broken() -> Missing:  # type: ignore[name-defined]  # noqa: F821
        pass  # pragma: no cover

    with pytest.raises(NameError):
        inspect.get_annotations(broken)


@py314
async def test_method_annotations_stay_lazy() -> None:
    class Api:
        @alru_cache(maxsize=1)
        async def get_foo(self) -> Foo:
            return Foo()

    class Foo:
        pass

    api = Api()
    assert isinstance(await api.get_foo(), Foo)
    assert inspect.get_annotations(api.get_foo) == {"return": Foo}
