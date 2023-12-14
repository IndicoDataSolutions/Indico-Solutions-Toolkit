import time
from functools import wraps
from random import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import TypeVar

    ReturnType = TypeVar("ReturnType")


class MaxRetriesExceeded(Exception):
    """
    Raised when a function has retried more than `count` number of times.
    """


def retry(
    *errors: "type[Exception]",
    count: int = 4,
    wait: float = 1,
    backoff: float = 4,
    jitter: float = 0.5,
) -> "Callable[[Callable[..., ReturnType]], Callable[..., ReturnType]]":
    """
    Decorate a function to automatically retry when it raises specific errors,
    apply exponential backoff and jitter to the wait time,
    and raise `MaxRetriesExceeded` after it retries too many times.

    By default, the decorated method will be retried up to 4 times over the course of
    ~2 minutes (waiting 1, 4, 16, and 64 seconds; plus up to 50% jitter)
    before raising `MaxRetriesExceeded` from the last error.

    Arguments:
        errors:  Retry the function when it raises one of these errors.
        count:   Retry the function this many times before raising `MaxRetriesExceeded`.
        wait:    Wait this many seconds after the first error before retrying.
        backoff: Multiply the wait time by this amount for each additional error.
        jitter:  Add a random amount of time (up to this percent as a decimal)
                 to the wait time to prevent simultaneous retries.
    """

    def retry_decorator(
        function: "Callable[..., ReturnType]",
    ) -> "Callable[..., ReturnType]":
        @wraps(function)
        def retrying_function(*args: object, **kwargs: object) -> "ReturnType":
            for times_retried in range(count + 1):
                try:
                    return function(*args, **kwargs)
                except errors as error:
                    last_error = error

                if times_retried >= count:
                    raise MaxRetriesExceeded() from last_error

                time.sleep(wait * backoff**times_retried * (1 + jitter * random()))

        return retrying_function

    return retry_decorator
