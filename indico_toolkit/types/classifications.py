from dataclasses import dataclass
from typing import TypeAlias

Label: TypeAlias = str


@dataclass
class Classification:
    model: str
    label: str
    confidences: dict[Label, float]

    @property
    def confidence(self) -> float:
        return self.confidences[self.label]

    @staticmethod
    def from_result(result: dict[str, object]) -> "Classification":
        """
        Factory function to produce a `Classification` from a portion of a result file.
        """
        ...
