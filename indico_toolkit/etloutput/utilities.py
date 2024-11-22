from typing import TypeVar

from .errors import EtlOutputError

Value = TypeVar("Value")


def get(result: object, value_type: "type[Value]", *keys: "str | int") -> Value:
    """
    Return the value obtained by traversing `result` using `keys` as indices if that
    value has type `value_type`. Raise a `EtlOutputError` otherwise.
    """
    for key in keys:
        if isinstance(key, str) and isinstance(result, dict) and key in result:
            result = result[key]
        elif isinstance(key, int) and isinstance(result, list) and key < len(result):
            result = result[key]
        else:
            raise EtlOutputError(
                f"etl output `{type(result)!r}` does not contain key `{key!r}`"
            )

    if isinstance(result, value_type):
        return result
    else:
        raise EtlOutputError(
            f"etl output `{type(result)!r}` does not have a value for "
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
