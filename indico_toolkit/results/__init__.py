import json
from typing import TYPE_CHECKING

from .document import Document
from .errors import ResultError
from .model import ModelGroup, TaskType
from .predictionlist import PredictionList
from .predictions import (
    NULL_BOX,
    NULL_CITATION,
    NULL_SPAN,
    Box,
    Classification,
    DocumentExtraction,
    Extraction,
    FormExtraction,
    FormExtractionType,
    Group,
    Prediction,
    Span,
    Summarization,
    Unbundling,
)
from .result import Result
from .review import Review, ReviewType
from .utilities import get

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


__all__ = (
    "Box",
    "Classification",
    "Document",
    "DocumentExtraction",
    "Extraction",
    "FormExtraction",
    "FormExtractionType",
    "Group",
    "load",
    "load_async",
    "ModelGroup",
    "NULL_BOX",
    "NULL_CITATION",
    "NULL_SPAN",
    "Prediction",
    "PredictionList",
    "Result",
    "ResultError",
    "Review",
    "ReviewType",
    "Span",
    "Summarization",
    "TaskType",
    "Unbundling",
)


def load(result: object, *, reader: "Callable[..., object] | None" = None) -> Result:
    """
    Load `result` as a Result dataclass.

    `result` can be a dict, a JSON string, or something that can be read with `reader`
    to produce either.

    ```
    for result_file in result_folder.glob("*.json"):
        result = results.load(result_file, reader=Path.read_text)
    ```
    """
    if reader:
        result = reader(result)

    return _load(result)


async def load_async(
    result: object, *, reader: "Callable[..., Awaitable[object]] | None" = None
) -> Result:
    """
    Load `result` as a Result dataclass.

    `result` can be a dict, a JSON string, or something that can be read with `reader`
    to produce either.
    """
    if reader:
        result = await reader(result)

    return _load(result)


def _load(result: object) -> Result:
    if isinstance(result, str) and result.strip().startswith("{"):
        result = json.loads(result)

    file_version = get(result, int, "file_version")

    if file_version == 1:
        return Result.from_v1_dict(result)
    elif file_version == 3:
        return Result.from_v3_dict(result)
    else:
        raise ResultError(f"unsupported file version `{file_version!r}`")
