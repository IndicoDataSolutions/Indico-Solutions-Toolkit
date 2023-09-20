from dataclasses import dataclass
from typing import TypeAlias

Label: TypeAlias = str


@dataclass
class Prediction:
    model: str
    text: str
    label: str
    confidences: dict[Label, float]

    @property
    def confidence(self) -> float:
        return self.confidences[self.label]

    def accept(self) -> None:
        """
        Mark prediction as accepted for Autoreview.
        """
        ...

    def reject(self) -> None:
        """
        Mark prediction as rejected for Autoreview.
        """
        ...

    @staticmethod
    def from_result(result: dict[str, object]) -> "Prediction":
        """
        Factory function to produce a `Prediction` from a portion of a result file.
        """
        ...
