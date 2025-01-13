import pytest

from indico_toolkit.retry import retry, MaxRetriesExceeded


def test_no_errors() -> None:
    @retry(Exception)
    def no_errors() -> bool:
        return True

    assert no_errors()


def test_raises_errors() -> None:
    calls = 0

    @retry(RuntimeError, count=4, wait=0)
    def raises_errors() -> None:
        nonlocal calls
        calls += 1
        raise RuntimeError()

    with pytest.raises(MaxRetriesExceeded):
        raises_errors()

    assert calls == 5


def test_raises_other_errors() -> None:
    calls = 0

    @retry(RuntimeError, count=4, wait=0)
    def raises_errors() -> None:
        nonlocal calls
        calls += 1
        raise ValueError()

    with pytest.raises(ValueError):
        raises_errors()

    assert calls == 1


@pytest.mark.asyncio
async def test_raises_errors_async() -> None:
    calls = 0

    @retry(RuntimeError, count=4, wait=0)
    async def raises_errors() -> None:
        nonlocal calls
        calls += 1
        raise RuntimeError()

    with pytest.raises(MaxRetriesExceeded):
        await raises_errors()

    assert calls == 5


@pytest.mark.asyncio
async def test_raises_other_errors_async() -> None:
    calls = 0

    @retry(RuntimeError, count=4, wait=0)
    async def raises_errors() -> None:
        nonlocal calls
        calls += 1
        raise ValueError()

    with pytest.raises(ValueError):
        await raises_errors()

    assert calls == 1
