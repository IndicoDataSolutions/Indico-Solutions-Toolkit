import pytest

from indico_toolkit.types import ResultFileError
from indico_toolkit.types.utils import exists, get, nfilter


def test_exists() -> None:
    result = {
        "int": 0,
        "list": [],
        "dict": {},
        "none": None,
    }

    assert exists(result, "int", int)
    assert not exists(result, "int", list)
    assert exists(result, "list", list)
    assert not exists(result, "list", dict)
    assert exists(result, "dict", dict)
    assert not exists(result, "dict", int)
    assert exists(result, "none", type(None))


def test_get() -> None:
    list_ = []
    dict_ = {}

    result = {
        "int": 0,
        "list": list_,
        "dict": dict_,
    }

    assert get(result, "int", int) == 0
    assert get(result, "list", list) is list_
    assert get(result, "dict", dict) is dict_

    with pytest.raises(ResultFileError):
        assert get(result, "int", list)

    with pytest.raises(ResultFileError):
        assert get(result, "none", list)


def test_nfilter() -> None:
    values = list(
        nfilter(
            [
                lambda s: s != "a",
                lambda s: s != "c",
            ],
            ["a", "b", "c"],
        )
    )

    assert values == ["b"]
