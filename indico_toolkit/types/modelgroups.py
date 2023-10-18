from dataclasses import dataclass
from enum import StrEnum

from .utils import get


class ModelType(StrEnum):
    CLASSIFICATION = "classification"
    EXTRACTION = "annotation"


@dataclass
class ModelGroup:
    id: int
    name: str
    type: ModelType

    @staticmethod
    def _from_result(model_group: object) -> "ModelGroup":
        return ModelGroup(
            id=get(model_group, "id", int),
            name=get(model_group, "name", str),
            type=ModelType(get(model_group, "task_type", str)),
        )
