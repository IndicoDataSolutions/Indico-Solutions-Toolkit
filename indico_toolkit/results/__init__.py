import json
from os import PathLike

from .documents import Document
from .errors import MultipleValuesError, ResultKeyError
from .lists import ClassificationList, ExtractionList, PredictionList, UnbundlingList
from .predictions import Classification, Extraction, Prediction, Unbundling
from .results import Result
from .reviews import Review, ReviewType
from .spans import Span

__all__ = (
    "Classification",
    "ClassificationList",
    "Document",
    "Extraction",
    "ExtractionList",
    "load",
    "MultipleValuesError",
    "Prediction",
    "PredictionList",
    "ResultKeyError",
    "Review",
    "ReviewType",
    "Span",
    "Result",
    "Unbundling",
    "UnbundlingList",
)


def load(result: object, *, convert_unreviewed: bool = False) -> Result:
    """
    Load a result file as a Result dataclass. `result` can be a dict from
    `RetrieveStorageObject`, a JSON string, or a path to a JSON file.

    Optionally convert unreviewed results, making predictions available via in
    `result.document.final`.
    """
    if isinstance(result, str) and result.startswith("{"):
        result = json.loads(result)
    elif isinstance(result, (str, PathLike)):
        with open(result) as file:
            result = json.load(file)

    return Result.from_result(result, convert_unreviewed=convert_unreviewed)
