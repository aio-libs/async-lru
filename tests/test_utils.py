from functools import partial

from async_lru import unpartial


def test_unpartial():
    def foo():
        pass

    assert unpartial(foo) is foo

    bar = partial(foo)

    assert unpartial(bar) is foo

    for _ in range(10):
        bar = partial(bar)

    assert unpartial(bar) is foo
