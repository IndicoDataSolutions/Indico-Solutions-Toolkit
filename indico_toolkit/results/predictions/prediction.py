from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..review import Review

if TYPE_CHECKING:
    from typing import Any

    from ..document import Document
    from ..model import ModelGroup


@dataclass
class Prediction:
    document: "Document"
    model: "ModelGroup"
    review: "Review | None"

    label: str
    confidences: "dict[str, float]"
    extras: "dict[str, Any]"

    @property
    def confidence(self) -> float:
        return self.confidences[self.label]

    @confidence.setter
    def confidence(self, value: float) -> None:
        self.confidences[self.label] = value

    def to_v1_dict(self) -> "dict[str, Any]":
        """
        Create a prediction dictionary for v1 auto review changes.
        """
        raise NotImplementedError()

    def to_v3_dict(self) -> "dict[str, Any]":
        """
        Create a prediction dictionary for v3 auto review changes.
        """
        raise NotImplementedError()
