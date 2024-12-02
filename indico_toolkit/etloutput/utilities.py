from typing import TypeVar

from .errors import EtlOutputError

Value = TypeVar("Value")


def get(nested: object, value_type: "type[Value]", *keys: "str | int") -> Value:
    """
    Return the value obtained by traversing `nested` using `keys` as indices if that
    value is of type `value_type`. Raise a `EtlOutputError` otherwise.
    """
    for key in keys:
        if isinstance(key, str) and isinstance(nested, dict) and key in nested:
            nested = nested[key]
        elif isinstance(key, int) and isinstance(nested, list) and key < len(nested):
            nested = nested[key]
        else:
            raise EtlOutputError(
                f"etl output `{type(nested)!r}` does not contain key `{key!r}`"
            )

    if isinstance(nested, value_type):
        return nested
    else:
        raise EtlOutputError(
            f"etl output `{type(nested)!r}` does not have a value for "
            f"key `{key!r}` of type `{value_type}`"
        )


def has(nested: object, value_type: "type[Value]", *keys: "str | int") -> bool:
    """
    Check if `nested` can be traversed using `keys` to a value of type `value_type`.
    """
    for key in keys:
        if isinstance(key, str) and isinstance(nested, dict) and key in nested:
            nested = nested[key]
        elif isinstance(key, int) and isinstance(nested, list) and key < len(nested):
            nested = nested[key]
        else:
            return False

    return isinstance(nested, value_type)
