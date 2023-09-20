from dataclasses import dataclass
from typing import TypeAlias

Label: TypeAlias = str


@dataclass
class Classification:
    model: str
    confidences: dict[Label, float]

    @property
    def label(self) -> str:
        highest_confidence_pair = sorted(
            self.confidences.items(), key=lambda pair: pair[1], reverse=True
        )[0]
        return highest_confidence_pair[0]

    @property
    def confidence(self) -> float:
        return self.confidences[self.label]

    @staticmethod
    def from_result(result: dict[str, object]) -> "Classification":
        """
        Factory function to produce a `Classification` from a portion of a result file.
        """
        ...
