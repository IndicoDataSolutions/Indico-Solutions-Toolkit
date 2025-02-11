from typing import TYPE_CHECKING

from ..model import ModelGroupType
from .box import NULL_BOX, Box
from .citation import NULL_CITATION, Citation
from .classification import Classification
from .documentextraction import DocumentExtraction
from .extraction import Extraction
from .formextraction import FormExtraction, FormExtractionType
from .group import Group
from .prediction import Prediction
from .span import NULL_SPAN, Span
from .summarization import Summarization
from .unbundling import Unbundling

if TYPE_CHECKING:
    from ..document import Document
    from ..errors import ResultError
    from ..model import ModelGroup
    from ..review import Review

__all__ = (
    "Box",
    "Citation",
    "Classification",
    "DocumentExtraction",
    "Extraction",
    "FormExtraction",
    "FormExtractionType",
    "Group",
    "NULL_BOX",
    "NULL_CITATION",
    "NULL_SPAN",
    "Prediction",
    "Span",
    "Summarization",
    "Unbundling",
)

CLASSIFICATION = ModelGroupType.CLASSIFICATION
DOCUMENT_EXTRACTION = ModelGroupType.DOCUMENT_EXTRACTION
FORM_EXTRACTION = ModelGroupType.FORM_EXTRACTION
GENAI_CLASSIFICATION = ModelGroupType.GENAI_CLASSIFICATION
GENAI_EXTRACTION = ModelGroupType.GENAI_EXTRACTION
GENAI_SUMMARIZATION = ModelGroupType.GENAI_SUMMARIZATION
UNBUNDLING = ModelGroupType.UNBUNDLING


def from_v1_dict(
    document: "Document",
    model: "ModelGroup",
    review: "Review | None",
    prediction: object,
) -> "Prediction":
    """
    Create a `Prediction` subclass from a v1 prediction dictionary.
    """
    if model.type == CLASSIFICATION:
        return Classification.from_v1_dict(document, model, review, prediction)
    elif model.type == DOCUMENT_EXTRACTION:
        return DocumentExtraction.from_v1_dict(document, model, review, prediction)
    elif model.type == FORM_EXTRACTION:
        return FormExtraction.from_v1_dict(document, model, review, prediction)
    else:
        raise ResultError(f"unsupported v1 model type `{model.type!r}`")


def from_v3_dict(
    document: "Document",
    model: "ModelGroup",
    review: "Review | None",
    prediction: object,
) -> "Prediction":
    """
    Create a `Prediction` subclass from a v3 prediction dictionary.
    """
    if model.type in (CLASSIFICATION, GENAI_CLASSIFICATION):
        return Classification.from_v3_dict(document, model, review, prediction)
    elif model.type in (DOCUMENT_EXTRACTION, GENAI_EXTRACTION):
        return DocumentExtraction.from_v3_dict(document, model, review, prediction)
    elif model.type == FORM_EXTRACTION:
        return FormExtraction.from_v3_dict(document, model, review, prediction)
    elif model.type == GENAI_SUMMARIZATION:
        return Summarization.from_v3_dict(document, model, review, prediction)
    elif model.type == UNBUNDLING:
        return Unbundling.from_v3_dict(document, model, review, prediction)
    else:
        raise ResultError(f"unsupported v3 model type `{model.type!r}`")
