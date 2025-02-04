from typing import TYPE_CHECKING

from ..model import TaskType
from .box import NULL_BOX, Box
from .classification import Classification
from .documentextraction import DocumentExtraction
from .extraction import Extraction
from .formextraction import FormExtraction, FormExtractionType
from .group import Group
from .prediction import Prediction
from .span import NULL_SPAN, Span
from .unbundling import Unbundling

if TYPE_CHECKING:
    from ..document import Document
    from ..errors import ResultError
    from ..model import ModelGroup
    from ..review import Review

__all__ = (
    "Box",
    "Classification",
    "DocumentExtraction",
    "Extraction",
    "FormExtraction",
    "FormExtractionType",
    "Group",
    "NULL_BOX",
    "NULL_SPAN",
    "Prediction",
    "Span",
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
    elif model.task_type == TaskType.DOCUMENT_EXTRACTION:
        return DocumentExtraction.from_v1_dict(document, model, review, prediction)
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
    elif model.task_type == TaskType.DOCUMENT_EXTRACTION:
        return DocumentExtraction.from_v3_dict(document, model, review, prediction)
    elif model.task_type == TaskType.FORM_EXTRACTION:
        return FormExtraction.from_v3_dict(document, model, review, prediction)
    elif model.task_type == TaskType.UNBUNDLING:
        return Unbundling.from_v3_dict(document, model, review, prediction)
    else:
        raise ResultError(f"unsupported v3 task type `{model.task_type!r}`")
