import asyncio
from asyncio.coroutines import _is_coroutine  # type: ignore[attr-defined]
from functools import _CacheInfo, _make_key, partial, partialmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Coroutine,
    Generic,
    Hashable,
    List,
    Optional,
    OrderedDict,
    Set,
    Type,
    TypeVar,
    Union,
    cast,
    overload,
)


if TYPE_CHECKING:
    # pypy doesn't support typing_extensions
    from typing_extensions import Self


__version__ = "2.0.0"

__all__ = ("alru_cache",)


_T = TypeVar("_T")
_R = TypeVar("_R")
_Coro = Coroutine[Any, Any, _R]
_CB = Callable[..., _Coro[_R]]
_CBP = Union[_CB[_R], "partial[_Coro[_R]]", "partialmethod[_Coro[_R]]"]


def _done_callback(fut: "asyncio.Future[_R]", task: "asyncio.Task[_R]") -> None:
    if task.cancelled():
        fut.cancel()
        return

    exc = task.exception()
    if exc is not None:
        fut.set_exception(exc)
        return

    fut.set_result(task.result())


class _LRUCacheWrapper(Generic[_R]):
    def __init__(
        self,
        fn: _CB[_R],
        maxsize: Optional[int],
        typed: bool,
        cache_exceptions: bool,
    ) -> None:
        try:
            self.__module__ = fn.__module__
        except AttributeError:
            pass
        try:
            self.__name__ = fn.__name__
        except AttributeError:
            pass
        try:
            self.__qualname__ = fn.__qualname__
        except AttributeError:
            pass
        try:
            self.__doc__ = fn.__doc__
        except AttributeError:
            pass
        try:
            self.__annotations__ = fn.__annotations__
        except AttributeError:
            pass
        try:
            self.__dict__.update(fn.__dict__)
        except AttributeError:
            pass
        # set __wrapped__ last so we don't inadvertently copy it
        # from the wrapped function when updating __dict__
        self._is_coroutine = _is_coroutine
        self.__wrapped__ = fn
        self.__maxsize = maxsize
        self.__typed = typed
        self.__cache_exceptions = cache_exceptions
        self.__cache: OrderedDict[Hashable, "asyncio.Future[_R]"] = OrderedDict()
        self.__closed = False
        self.__hits = 0
        self.__misses = 0
        self.__tasks: Set["asyncio.Task[_R]"] = set()

    @property
    def hits(self) -> int:
        return self.__hits

    @property
    def misses(self) -> int:
        return self.__misses

    @property
    def tasks(self) -> Set["asyncio.Task[_R]"]:
        return set(self.__tasks)

    @property
    def closed(self) -> int:
        return self.__closed

    def invalidate(self, /, *args: Hashable, **kwargs: Any) -> bool:
        key = _make_key(args, kwargs, self.__typed)

        exists = key in self.__cache

        if exists:
            self.__cache.pop(key)

        return exists

    def cache_clear(self) -> None:
        self.__hits = 0
        self.__misses = 0
        self.__cache.clear()
        self.__tasks.clear()

    def open(self) -> None:
        if not self.__closed:
            raise RuntimeError("alru_cache is not closed")

        was_closed = (
            self.__hits == self.__misses == len(self.__tasks) == len(self.__cache) == 0
        )

        if not was_closed:
            raise RuntimeError("alru_cache was not closed correctly")

        self.__closed = False

    def close(
        self, *, cancel: bool = False, return_exceptions: bool = True
    ) -> Awaitable[List[_R]]:
        if self.__closed:
            raise RuntimeError("alru_cache is closed")

        self.__closed = True

        if cancel:
            for task in self.__tasks:
                if not task.done():  # not sure is it possible
                    task.cancel()

        return self._wait_closed(return_exceptions=return_exceptions)

    async def _wait_closed(self, *, return_exceptions: bool) -> List[_R]:
        wait_closed = asyncio.gather(*self.tasks, return_exceptions=return_exceptions)

        wait_closed.add_done_callback(self._close_waited)

        ret = await wait_closed

        # hack to get _close_waited callback to be executed
        await asyncio.sleep(0)

        return ret

    def _close_waited(self, fut: "asyncio.Future[List[_R]]") -> None:
        self.cache_clear()

    def cache_info(self) -> _CacheInfo:
        return _CacheInfo(
            self.__hits,
            self.__misses,
            self.__maxsize,  # type: ignore[arg-type]
            len(self.__cache),
        )

    def __cache_touch(self, key: Hashable) -> None:
        try:
            self.__cache.move_to_end(key)
        except KeyError:  # not sure is it possible
            pass

    def _cache_hit(self, key: Hashable) -> None:
        self.__hits += 1
        self.__cache_touch(key)

    def _cache_miss(self, key: Hashable) -> None:
        self.__misses += 1
        self.__cache_touch(key)

    async def __call__(self, /, *fn_args: Any, **fn_kwargs: Any) -> _R:
        if self.__closed:
            raise RuntimeError("alru_cache is closed for {}".format(self))

        loop = asyncio.get_event_loop()

        key = _make_key(fn_args, fn_kwargs, self.__typed)

        fut = self.__cache.get(key)

        if fut is not None:
            if not fut.done():
                self._cache_hit(key)
                return await asyncio.shield(fut)

            exc = fut._exception

            if exc is None or self.__cache_exceptions:
                self._cache_hit(key)
                return fut.result()

            # exception here and cache_exceptions == False
            self.__cache.pop(key)

        fut = loop.create_future()
        coro = self.__wrapped__(*fn_args, **fn_kwargs)
        task: asyncio.Task[_R] = loop.create_task(coro)
        task.add_done_callback(partial(_done_callback, fut))

        self.__tasks.add(task)
        task.add_done_callback(self.__tasks.remove)

        self.__cache[key] = fut

        if self.__maxsize is not None and len(self.__cache) > self.__maxsize:
            self.__cache.popitem(last=False)

        self._cache_miss(key)
        return await asyncio.shield(fut)

    def __get__(
        self, instance: _T, owner: Optional[Type[_T]]
    ) -> Union["Self", "_LRUCacheWrapperInstanceMethod[_R, _T]"]:
        if owner is None:
            return self
        else:
            return _LRUCacheWrapperInstanceMethod(self, instance)


class _LRUCacheWrapperInstanceMethod(Generic[_R, _T]):
    def __init__(
        self,
        wrapper: _LRUCacheWrapper[_R],
        instance: _T,
    ) -> None:
        try:
            self.__module__ = wrapper.__module__
        except AttributeError:
            pass
        try:
            self.__name__ = wrapper.__name__
        except AttributeError:
            pass
        try:
            self.__qualname__ = wrapper.__qualname__
        except AttributeError:
            pass
        try:
            self.__doc__ = wrapper.__doc__
        except AttributeError:
            pass
        try:
            self.__annotations__ = wrapper.__annotations__
        except AttributeError:
            pass
        try:
            self.__dict__.update(wrapper.__dict__)
        except AttributeError:
            pass
        # set __wrapped__ last so we don't inadvertently copy it
        # from the wrapped function when updating __dict__
        self._is_coroutine = _is_coroutine
        self.__wrapped__ = wrapper.__wrapped__
        self.__instance = instance
        self.__wrapper = wrapper

    @property
    def hits(self) -> int:
        return self.__wrapper.hits

    @property
    def misses(self) -> int:
        return self.__wrapper.misses

    @property
    def tasks(self) -> Set["asyncio.Task[_R]"]:
        return self.__wrapper.tasks

    @property
    def closed(self) -> int:
        return self.__wrapper.closed

    def invalidate(self, /, *args: Hashable, **kwargs: Any) -> bool:
        return self.__wrapper.invalidate(*args, **kwargs)

    def cache_clear(self) -> None:
        self.__wrapper.cache_clear()

    def open(self) -> None:
        return self.__wrapper.open()

    def close(
        self, *, cancel: bool = False, return_exceptions: bool = True
    ) -> Awaitable[List[_R]]:
        return self.__wrapper.close()

    def cache_info(self) -> _CacheInfo:
        return self.__wrapper.cache_info()

    async def __call__(self, /, *fn_args: Any, **fn_kwargs: Any) -> _R:
        return await self.__wrapper(self.__instance, *fn_args, **fn_kwargs)


def _make_wrapper(
    maxsize: Optional[int], typed: bool, cache_exceptions: bool
) -> Callable[[_CBP[_R]], _LRUCacheWrapper[_R]]:
    def wrapper(fn: _CBP[_R]) -> _LRUCacheWrapper[_R]:
        origin = fn

        while isinstance(origin, (partial, partialmethod)):
            origin = origin.func

        if not asyncio.iscoroutinefunction(origin):
            raise RuntimeError("Coroutine function is required, got {!r}".format(fn))

        # functools.partialmethod support
        if hasattr(fn, "_make_unbound_method"):
            fn = fn._make_unbound_method()

        return _LRUCacheWrapper(cast(_CB[_R], fn), maxsize, typed, cache_exceptions)

    return wrapper


@overload
def alru_cache(
    maxsize: Optional[int] = 128, typed: bool = False, *, cache_exceptions: bool = False
) -> Callable[[_CBP[_R]], _LRUCacheWrapper[_R]]:
    ...


@overload
def alru_cache(
    maxsize: _CBP[_R],
    /,
) -> _LRUCacheWrapper[_R]:
    ...


def alru_cache(
    maxsize: Union[Optional[int], _CBP[_R]] = 128,
    typed: bool = False,
    *,
    cache_exceptions: bool = True,
) -> Union[Callable[[_CBP[_R]], _LRUCacheWrapper[_R]], _LRUCacheWrapper[_R]]:
    if maxsize is None or isinstance(maxsize, int):
        return _make_wrapper(maxsize, typed, cache_exceptions)
    else:
        fn = cast(_CB[_R], maxsize)

        if callable(fn) or hasattr(fn, "_make_unbound_method"):
            return _make_wrapper(128, False, True)(fn)

        raise NotImplementedError("{!r} decorating is not supported".format(fn))
