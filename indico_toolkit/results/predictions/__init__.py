from typing import TYPE_CHECKING

from ..models import TaskType
from .autoreviewable import AutoReviewable
from .classifications import Classification
from .extractions import Extraction
from .formextractions import FormExtraction, FormExtractionType
from .groups import Group
from .predictions import Prediction
from .unbundlings import Unbundling

if TYPE_CHECKING:
    from ..documents import Document
    from ..errors import ResultError
    from ..models import ModelGroup
    from ..reviews import Review

__all__ = (
    "AutoReviewable",
    "Classification",
    "Extraction",
    "FormExtraction",
    "FormExtractionType",
    "Group",
    "Prediction",
    "Unbundling",
)


def from_v1_dict(
    document: "Document",
    model: "ModelGroup",
    review: "Review | None",
    prediction: object,
) -> "Prediction":
    """
    Create a `Prediction` subclass from a v1 prediction dictionary.
    """
    if model.task_type == TaskType.CLASSIFICATION:
        return Classification.from_v1_dict(document, model, review, prediction)
    elif model.task_type == TaskType.EXTRACTION:
        return Extraction.from_v1_dict(document, model, review, prediction)
    elif model.task_type == TaskType.FORM_EXTRACTION:
        return FormExtraction.from_v1_dict(document, model, review, prediction)
    else:
        raise ResultError(f"unsupported v1 task type `{model.task_type!r}`")


def from_v3_dict(
    document: "Document",
    model: "ModelGroup",
    review: "Review | None",
    prediction: object,
) -> "Prediction":
    """
    Create a `Prediction` subclass from a v3 prediction dictionary.
    """
    if model.task_type == TaskType.CLASSIFICATION:
        return Classification.from_v3_dict(document, model, review, prediction)
    elif model.task_type == TaskType.EXTRACTION:
        return Extraction.from_v3_dict(document, model, review, prediction)
    elif model.task_type == TaskType.FORM_EXTRACTION:
        return FormExtraction.from_v3_dict(document, model, review, prediction)
    elif model.task_type == TaskType.UNBUNDLING:
        return Unbundling.from_v3_dict(document, model, review, prediction)
    else:
        raise ResultError(f"unsupported v3 task type `{model.task_type!r}`")
