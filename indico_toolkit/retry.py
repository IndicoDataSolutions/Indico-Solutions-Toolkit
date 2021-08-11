from functools import wraps
import time


def retry(exceptions, num_retries=5, wait=0.5):
    """
    Decorator for retrying functions after specified exceptions are raised
    Args:
    exceptions (Exception or Tuple[Exception]): exceptions that should be retried on
    wait (float): time in seconds to wait before retrying
    num_retries (int): the number of times to retry the wrapped function
    """
    def retry_decorator(fn):
        @wraps(fn)
        def retry_func(*args, **kwargs):
            retries = 0
            while True:
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    if retries >= num_retries:
                        raise e
                    else:
                        retries += 1
                        time.sleep(wait)
        return retry_func
    return retry_decorator