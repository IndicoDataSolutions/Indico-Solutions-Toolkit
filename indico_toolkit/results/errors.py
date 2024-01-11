class MultipleValuesError(Exception):
    """
    Raised when trying to access a collection that contains mutliple values
    as if it has a single value.
    """


class ResultFileError(Exception):
    """
    Raised when a result file dictionary is missing structures or
    values required to load it.
    """
