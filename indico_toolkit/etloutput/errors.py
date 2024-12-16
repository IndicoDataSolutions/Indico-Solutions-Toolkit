class EtlOutputError(Exception):
    """
    Raised when an error occurs while loading an ETL Output file.
    """


class TokenNotFoundError(EtlOutputError):
    """
    Raised when a Token can't be found for a Prediction.
    """


class TableCellNotFoundError(EtlOutputError):
    """
    Raised when a Table Cell can't be found for a Token.
    """
