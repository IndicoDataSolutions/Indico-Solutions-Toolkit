import json
from os import PathLike

from .documents import Document
from .errors import ResultError
from .lists import PredictionList
from .models import ModelGroup, TaskType
from .predictions import (
    Classification,
    DocumentExtraction,
    Extraction,
    FormExtraction,
    FormExtractionType,
    Group,
    Prediction,
    Unbundling,
)
from .results import Result
from .reviews import Review, ReviewType
from .utils import get

__all__ = (
    "Classification",
    "Document",
    "DocumentExtraction",
    "Extraction",
    "FormExtraction",
    "FormExtractionType",
    "Group",
    "ModelGroup",
    "Prediction",
    "PredictionList",
    "Result",
    "ResultError",
    "Review",
    "ReviewType",
    "TaskType",
    "Unbundling",
)


def load(result: object) -> Result:
    """
    Load `result` as a Result dataclass. `result` can be a dict from
    `RetrieveStorageObject`, a JSON string, or a path to a JSON file.
    """
    if isinstance(result, str) and result.strip().startswith("{"):
        result = json.loads(result)
    elif isinstance(result, (str, PathLike)):
        with open(result) as file:
            result = json.load(file)

    file_version = get(result, int, "file_version")

    if file_version == 1:
        return Result.from_v1_dict(result)
    elif file_version == 3:
        return Result.from_v3_dict(result)
    else:
        raise ResultError(f"unsupported file version `{file_version!r}`")
