import asyncio
import time
from functools import wraps
from inspect import iscoroutinefunction
from random import random
from typing import TYPE_CHECKING, overload

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from typing import ParamSpec, TypeVar

    ArgumentsType = ParamSpec("ArgumentsType")
    OuterReturnType = TypeVar("OuterReturnType")
    InnerReturnType = TypeVar("InnerReturnType")


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
) -> "Callable[[Callable[ArgumentsType, OuterReturnType]], Callable[ArgumentsType, OuterReturnType]]":  # noqa: E501
    """
    Decorate a function or coroutine to retry when it raises specified errors,
    apply exponential backoff and jitter to the wait time,
    and raise `MaxRetriesExceeded` after it retries too many times.

    By default, the decorated function or coroutine will be retried up to 4 times over
    the course of ~2 minutes (waiting 1, 4, 16, and 64 seconds; plus up to 50% jitter)
    before raising `MaxRetriesExceeded` from the last error.

    Arguments:
        errors:  Retry the function when it raises one of these errors.
        count:   Retry the function this many times before raising `MaxRetriesExceeded`.
        wait:    Wait this many seconds after the first error before retrying.
        backoff: Multiply the wait time by this amount for each additional error.
        jitter:  Add a random amount of time (up to this percent as a decimal)
                 to the wait time to prevent simultaneous retries.
    """

    def wait_time(times_retried: int) -> float:
        """
        Calculate the sleep time based on number of times retried.
        """
        return wait * backoff**times_retried * (1 + jitter * random())

    @overload
    def retry_decorator(
        decorated: "Callable[ArgumentsType, Awaitable[InnerReturnType]]",
    ) -> "Callable[ArgumentsType, Awaitable[InnerReturnType]]": ...
    @overload
    def retry_decorator(
        decorated: "Callable[ArgumentsType, InnerReturnType]",
    ) -> "Callable[ArgumentsType, InnerReturnType]": ...
    def retry_decorator(
        decorated: "Callable[ArgumentsType, InnerReturnType]",
    ) -> "Callable[ArgumentsType, Awaitable[InnerReturnType]] | Callable[ArgumentsType, InnerReturnType]":  # noqa: E501
        """
        Decorate either a function or coroutine as appropriate.
        """
        if iscoroutinefunction(decorated):

            @wraps(decorated)
            async def retrying_coroutine(  # type: ignore[return]
                *args: "ArgumentsType.args", **kwargs: "ArgumentsType.kwargs"
            ) -> "InnerReturnType":
                for times_retried in range(count + 1):
                    try:
                        return await decorated(*args, **kwargs)  # type: ignore[no-any-return]
                    except errors as error:
                        last_error = error

                    if times_retried >= count:
                        raise MaxRetriesExceeded() from last_error

                    await asyncio.sleep(wait_time(times_retried))

            return retrying_coroutine
        else:

            @wraps(decorated)
            def retrying_function(  # type: ignore[return]
                *args: "ArgumentsType.args", **kwargs: "ArgumentsType.kwargs"
            ) -> "InnerReturnType":
                for times_retried in range(count + 1):
                    try:
                        return decorated(*args, **kwargs)
                    except errors as error:
                        last_error = error

                    if times_retried >= count:
                        raise MaxRetriesExceeded() from last_error

                    time.sleep(wait_time(times_retried))

            return retrying_function

    return retry_decorator
