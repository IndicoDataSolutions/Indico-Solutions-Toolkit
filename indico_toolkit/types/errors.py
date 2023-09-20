class MultiValueError(Exception):
    """
    Raised when trying to access a single value of collection with mutliple values.
    """


class ResultError(Exception):
    """
    Raised when a result file dictionary is missing the structure or values
    required to parse it into a `Submission` object.
    """
