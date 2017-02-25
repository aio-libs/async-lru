import asyncio
from collections import OrderedDict, namedtuple
from functools import _make_key, partial, wraps

_CacheInfo = namedtuple('CacheInfo', ['hits', 'misses', 'maxsize', 'currsize'])


def get_wrapped_fn(fn):
    while hasattr(fn, '__wrapped__'):
        fn = fn.__wrapped__

    return fn


def create_future(*, loop):
    try:
        return loop.create_future()
    except AttributeError:
        return asyncio.Future(loop=loop)


def create_task(*, loop):
    try:
        return loop.create_task
    except AttributeError:
        try:
            return partial(asyncio.ensure_future, loop=loop)
        except AttributeError:
            return partial(getattr(asyncio, 'async'), loop=loop)


def iscoroutinepartial(fn):
    # http://bugs.python.org/issue23519

    while True:
        parent = fn

        fn = getattr(parent, 'func', None)

        if fn is None:
            break

    return asyncio.iscoroutinefunction(parent)


def _done_callback(fut, coro):
    raised = coro.exception()

    if raised is None:
        fut.set_result(coro.result())
    else:
        fut.set_exception(raised)


def _cache_invalidate(cache, typed, *args, **kwargs):
    key = _make_key(args, kwargs, typed)

    exists = key in cache

    if exists:
        cache.pop(key)

    return exists


def _cache_clear(wrapped):
    wrapped.hits = wrapped.misses = 0
    wrapped.cache.clear()


@asyncio.coroutine
def _wait_closed(wrapped, *, loop=None):
    if loop is None:
        loop = asyncio.get_event_loop()

    try:
        yield from asyncio.gather(*wrapped.coros, loop=loop)
    except asyncio.CancelledError:
        pass
    finally:
        wrapped.closing = False


def _close(wrapped, cancel=True):
    if wrapped.closing:
        raise RuntimeError('alru_cache is closing')

    wrapped.closing = True

    if cancel:
        for coro in wrapped.coros:
            coro.cancel()


def alru_cache(fn=None, maxsize=128, typed=False, *, loop=None):
    def wrapper(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if wrapped.closing:
                raise RuntimeError('alru_cache is closed')

            if isinstance(loop, str):
                self = getattr(get_wrapped_fn(fn), '__self__', None)
                if self is None:
                    assert args
                    self = args[0]

                _loop = getattr(self, loop)
            elif loop is None:
                _loop = asyncio.get_event_loop()
            else:
                _loop = loop

            key = _make_key(args, kwargs, typed)

            if key in wrapped.cache:
                wrapped.hits += 1
                wrapped.cache.move_to_end(key)

                return wrapped.cache[key]
            else:
                fut = create_future(loop=_loop)

                ret = fn(*args, **kwargs)

                if iscoroutinepartial(fn):
                    coro = create_task(loop=_loop)(ret)
                    coro.add_done_callback(partial(_done_callback, fut))

                    wrapped.coros.add(coro)
                    coro.add_done_callback(wrapped.coros.remove)
                else:
                    fut.set_result(ret)

                wrapped.cache[key] = fut
                wrapped.misses += 1

                if maxsize is not None and len(wrapped.cache) > maxsize:
                    wrapped.cache.popitem(last=False)

                return fut

        wrapped.cache = OrderedDict()
        wrapped.hits = wrapped.misses = 0
        wrapped.cache_info = lambda: _CacheInfo(
            wrapped.hits,
            wrapped.misses,
            maxsize,
            len(wrapped.cache),
        )
        wrapped.cache_clear = partial(_cache_clear, wrapped)
        wrapped.coros = set()
        wrapped.closing = False

        wrapped.invalidate = partial(_cache_invalidate, wrapped.cache, typed)
        wrapped.close = partial(_close, wrapped)
        wrapped.wait_closed = partial(_wait_closed, wrapped)

        return wrapped

    if fn is None:
        return wrapper

    if callable(fn):
        return wrapper(fn)

    raise NotImplementedError
