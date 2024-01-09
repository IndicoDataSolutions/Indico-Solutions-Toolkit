import json
from os import PathLike

from .documents import Document
from .errors import MultipleValuesError, ResultFileError
from .lists import ClassificationList, ExtractionList, PredictionList
from .predictions import Classification, Extraction, Prediction
from .reviews import Review, ReviewType
from .spans import Span
from .submissions import Submission

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
    "ResultFileError",
    "Review",
    "ReviewType",
    "Span",
    "Submission",
)


def load(result: object) -> Submission:
    """
    Load a result file as a Submission dataclass. `result` can be a dict from
    `RetrieveStorageObject`, a JSON string, or a path to a JSON file.
    """
    if isinstance(result, str) and result.startswith("{"):
        result = json.loads(result)
    elif isinstance(result, (str, PathLike)):
        with open(result) as file:
            result = json.load(file)

    return Submission.from_result(result)
