import asyncio
from collections import OrderedDict
from functools import _CacheInfo, _make_key, partial, wraps

try:
    from asyncio import ensure_future
except ImportError:  # pragma: no cover
    ensure_future = getattr(asyncio, 'async')

__version__ = '0.1.0'


def create_future(*, loop):
    try:
        return loop.create_future()
    except AttributeError:
        return asyncio.Future(loop=loop)


def unpartial(fn):
    while hasattr(fn, 'func'):
        fn = fn.func

    return fn


def _done_callback(fut, task):
    if task.cancelled():
        fut.cancel()
        return

    exc = task.exception()
    if exc is not None:
        fut.set_exception(exc)
        return

    fut.set_result(task.result())


def _cache_invalidate(wrapped, typed, *args, **kwargs):
    key = _make_key(args, kwargs, typed)

    exists = key in wrapped._cache

    if exists:
        wrapped._cache.pop(key)

    return exists


def _cache_clear(wrapped):
    wrapped.hits = wrapped.misses = 0
    wrapped._cache = OrderedDict()
    wrapped.tasks = set()


def _open(wrapped):
    if not wrapped.closed:
        raise RuntimeError('alru_cache is not closed')

    wrapped.closed = False


def _close(wrapped, *, cancel=False, return_exceptions=True, loop=None):
    if wrapped.closed:
        raise RuntimeError('alru_cache is closed')

    wrapped.closed = True

    if cancel:
        for task in wrapped.tasks:
            task.cancel()

    return _wait_closed(
        wrapped,
        return_exceptions=return_exceptions,
        loop=loop
    )


@asyncio.coroutine
def _wait_closed(wrapped, *, return_exceptions, loop):
    if loop is None:
        loop = asyncio.get_event_loop()

    wait_closed = asyncio.gather(
        *wrapped.tasks,
        return_exceptions=return_exceptions,
        loop=loop
    )

    wait_closed.add_done_callback(partial(__wait_closed, wrapped))

    return (yield from wait_closed)


def __wait_closed(wrapped, _):
    wrapped.cache_clear()


def _cache_info(wrapped, maxsize):
    return _CacheInfo(
        wrapped.hits,
        wrapped.misses,
        maxsize,
        len(wrapped._cache),
    )


def __cache_touch(wrapped, key, fut, *, loop):
    wrapped._cache.move_to_end(key)
    return asyncio.shield(fut, loop=loop)


def _cache_hit(wrapped, key, fut, *, loop):
    wrapped.hits += 1
    return __cache_touch(wrapped, key, fut, loop=loop)


def _cache_miss(wrapped, key, fut, *, loop):
    wrapped.misses += 1
    return __cache_touch(wrapped, key, fut, loop=loop)


def _get_loop(cls, kwargs, fn, fn_args, fn_kwargs, *, loop):
    if isinstance(loop, str):
        assert cls ^ kwargs, 'choose self.loop or kwargs["loop"]'

        if cls:
            _self = getattr(fn, '__self__', None)

            if _self is None:
                assert fn_args, 'seems not unbound function'
                _self = fn_args[0]

            _loop = getattr(_self, loop)
        else:
            _loop = fn_kwargs[loop]
    elif loop is None:
        _loop = asyncio.get_event_loop()
    else:
        _loop = loop

    return _loop


def alru_cache(
    fn=None,
    maxsize=128,
    typed=False,
    *,
    cls=False,
    kwargs=False,
    cache_exceptions=True,
    loop=None
):
    def wrapper(fn):
        _origin = unpartial(fn)

        if not asyncio.iscoroutinefunction(_origin):
            raise RuntimeError('Coroutine function is required')

        @wraps(fn)
        @asyncio.coroutine
        def wrapped(*fn_args, **fn_kwargs):
            if wrapped.closed:
                raise RuntimeError('alru_cache is closed')

            _loop = _get_loop(
                cls,
                kwargs,
                wrapped._origin,
                fn_args,
                fn_kwargs,
                loop=loop
            )

            key = _make_key(fn_args, fn_kwargs, typed)

            fut = wrapped._cache.get(key)

            if fut is not None:
                if not fut.done():
                    ret = _cache_hit(wrapped, key, fut, loop=_loop)
                    return (yield from ret)

                exc = fut._exception

                if exc is None or cache_exceptions:
                    ret = _cache_hit(wrapped, key, fut, loop=_loop)
                    return (yield from ret)

                # exception here and cache_exceptions == False
                wrapped._cache.pop(key)

            fut = create_future(loop=_loop)

            coro = fn(*fn_args, **fn_kwargs)
            task = ensure_future(coro, loop=_loop)
            task.add_done_callback(partial(_done_callback, fut))

            wrapped.tasks.add(task)
            task.add_done_callback(wrapped.tasks.remove)

            wrapped._cache[key] = task

            if maxsize is not None and len(wrapped._cache) > maxsize:
                wrapped._cache.popitem(last=False)

            ret = _cache_miss(wrapped, key, fut, loop=_loop)
            return (yield from ret)

        _cache_clear(wrapped)
        wrapped._origin = _origin
        wrapped.closed = False
        wrapped.cache_info = partial(_cache_info, wrapped, maxsize)
        wrapped.cache_clear = partial(_cache_clear, wrapped)
        wrapped.invalidate = partial(_cache_invalidate, wrapped, typed)
        wrapped.close = partial(_close, wrapped)
        wrapped.open = partial(_open, wrapped)

        return wrapped

    if fn is None:
        return wrapper

    if callable(fn):
        return wrapper(fn)

    raise NotImplementedError
