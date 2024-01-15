from collections.abc import Iterable, Iterator
from typing import Callable, TypeVar

from .errors import ResultFileError

Value = TypeVar("Value")


def exists(result: object, key: str, value_type: "type[Value]") -> bool:
    """
    Check if `key` exists in `result` having type `value_type`.
    """
    return (
        isinstance(result, dict)
        and key in result
        and isinstance(result[key], value_type)
    )


def get(result: object, key: str, value_type: "type[Value]") -> Value:
    """
    Return the value of `key` from `result` if `result` is a dict and the value has type
    `value_type`. Raise a `ResultFileError` otherwise.
    """
    if exists(result, key, value_type):
        return result[key]  # type: ignore[index, no-any-return]
    else:
        raise ResultFileError(
            f"Result object `{type(result)!r}` does not have a value for "
            f"key `{key!r}` with type `{value_type}`."
        )


def nfilter(
    predicates: "Iterable[Callable[[Value], bool]]", values: "Iterable[Value]"
) -> "Iterator[Value]":
    """
    Apply multiple filter predicates to a iterable of values.

    `nfilter([first, second, third], values)` is equivalent to
    `filter(third, filter(second, filter(first, values)))`.
    """
    for predicate in predicates:
        values = filter(predicate, values)

    yield from values
