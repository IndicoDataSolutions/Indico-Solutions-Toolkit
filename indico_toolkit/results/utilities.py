from collections.abc import Iterable, Iterator
from typing import Callable, TypeVar

from .errors import ResultError

Value = TypeVar("Value")


def get(result: object, value_type: "type[Value]", *keys: "str | int") -> Value:
    """
    Return the value obtained by traversing `result` using `keys` as indices if that
    value has type `value_type`. Raise a `ResultError` otherwise.
    """
    for key in keys:
        if isinstance(key, str) and isinstance(result, dict) and key in result:
            result = result[key]
        elif isinstance(key, int) and isinstance(result, list) and key < len(result):
            result = result[key]
        else:
            raise ResultError(
                f"result object `{type(result)!r}` does not contain key `{key!r}`"
            )

    if isinstance(result, value_type):
        return result
    else:
        raise ResultError(
            f"result object `{type(result)!r}` does not have a value for "
            f"key `{key!r}` of type `{value_type}`"
        )


def has(result: object, value_type: "type[Value]", *keys: "str | int") -> bool:
    """
    Check if `result` can be traversed using `keys` to a value of type `value_type`.
    """
    for key in keys:
        if isinstance(key, str) and isinstance(result, dict) and key in result:
            result = result[key]
        elif isinstance(key, int) and isinstance(result, list) and key < len(result):
            result = result[key]
        else:
            return False

    return isinstance(result, value_type)


def nfilter(
    predicates: "Iterable[Callable[[Value], bool]]", values: "Iterable[Value]"
) -> "Iterator[Value]":
    """
    Apply multiple filter predicates to an iterable of values.

    `nfilter([first, second, third], values)` is equivalent to
    `filter(third, filter(second, filter(first, values)))`.
    """
    for predicate in predicates:
        values = filter(predicate, values)

    yield from values


def omit(dictionary: object, *keys: str) -> "dict[str, Value]":
    """
    Return a shallow copy of `dictionary` with `keys` omitted.
    """
    if not isinstance(dictionary, dict):
        return {}
    return {
        key: value
        for key, value in dictionary.items()
        if key not in keys
    }  # fmt: skip
