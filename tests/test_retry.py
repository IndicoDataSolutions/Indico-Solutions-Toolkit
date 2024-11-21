import pytest

from indico_toolkit.retry import retry, MaxRetriesExceeded


@retry(Exception)
def no_exceptions():
    return True


def test_retry_decorator_returns() -> None:
    assert no_exceptions() is True


calls = 0


@retry(RuntimeError, count=5, wait=0)
def raises_exceptions():
    global calls
    calls += 1
    raise RuntimeError()


def test_retry_max_exceeded() -> None:
    global calls
    calls = 0

    with pytest.raises(MaxRetriesExceeded):
        raises_exceptions()

    assert calls == 6
