import json
from os import PathLike

from .documents import Document
from .errors import MultipleValuesError, ResultFileError
from .lists import ClassificationList, ExtractionList, PredictionList, UnbundlingList
from .predictions import Classification, Extraction, Prediction, Unbundling
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
    "Unbundling",
    "UnbundlingList",
)


def load(result: object, *, convert_unreviewed: bool = False) -> Submission:
    """
    Load a result file as a Submission dataclass. `result` can be a dict from
    `RetrieveStorageObject`, a JSON string, or a path to a JSON file.

    Optionally convert unreviewed submissions, making predictions available via in
    `submission.document.final`.
    """
    if isinstance(result, str) and result.startswith("{"):
        result = json.loads(result)
    elif isinstance(result, (str, PathLike)):
        with open(result) as file:
            result = json.load(file)

    if convert_unreviewed and Submission.is_unreviewed_result(result):
        result = Submission.convert_to_reviewed_result(result)

    return Submission.from_result(result)
