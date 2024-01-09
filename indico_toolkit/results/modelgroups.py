from dataclasses import dataclass
from enum import StrEnum

from .utils import get


class ModelType(StrEnum):
    CLASSIFICATION = "classification"
    EXTRACTION = "annotation"
    UNBUNDLING = "classification_unbundling"


@dataclass
class ModelGroup:
    id: int
    name: str
    type: ModelType

    @staticmethod
    def _from_v2_result(model_group: object) -> "ModelGroup":
        """
        Bundled Submission Workflows.
        """
        return ModelGroup(
            id=get(model_group, "id", int),
            name=get(model_group, "name", str),
            type=ModelType(get(model_group, "task_type", str)),
        )

    @classmethod
    def _from_v3_result(cls, model_group: object) -> "ModelGroup":
        """
        Classify+Unbundle Workflows.
        """
        return cls._from_v2_result(model_group)
