from dataclasses import dataclass
from enum import Enum

from .utilities import get, has


class ModelGroupType(Enum):
    CLASSIFICATION = "classification"
    DOCUMENT_EXTRACTION = "annotation"
    FORM_EXTRACTION = "form_extraction"
    GENAI_CLASSIFICATION = "genai_classification"
    GENAI_EXTRACTION = "genai_annotation"
    GENAI_SUMMARIZATION = "summarization"
    UNBUNDLING = "classification_unbundling"


@dataclass(frozen=True, order=True)
class ModelGroup:
    id: int
    name: str
    type: ModelGroupType

    @staticmethod
    def from_v1_section(section: "tuple[str, object]") -> "ModelGroup":
        """
        Create a `ModelGroup` from a v1 prediction section.
        Use a heuristic on the first prediction of the model to determine its type.
        """
        name, predictions = section

        if has(predictions, dict, "pre_review", 0):
            prediction = get(predictions, dict, "pre_review", 0)

            if has(prediction, str, "type"):
                type = ModelGroupType.FORM_EXTRACTION
            elif has(prediction, str, "text"):
                type = ModelGroupType.DOCUMENT_EXTRACTION
            else:
                type = ModelGroupType.CLASSIFICATION
        else:
            # Likely an extraction model that produced no predictions.
            type = ModelGroupType.DOCUMENT_EXTRACTION

        return ModelGroup(
            # v1 result files don't include model IDs.
            id=None,  # type: ignore[arg-type]
            name=name,
            type=type,
        )

    @staticmethod
    def from_v3_dict(model_group: object) -> "ModelGroup":
        """
        Create a `ModelGroup` from a v3 model group dictionary.
        """
        return ModelGroup(
            id=get(model_group, int, "id"),
            name=get(model_group, str, "name"),
            type=ModelGroupType(get(model_group, str, "task_type")),
        )
