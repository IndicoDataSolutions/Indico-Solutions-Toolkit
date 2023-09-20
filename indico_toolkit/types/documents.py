from dataclasses import dataclass
from typing import TypeAlias

from .classifications import Classification
from .errors import MultiValueError
from .lists import PredictionList

ModelName: TypeAlias = str


@dataclass
class Document:
    id: int
    filename: str
    classifications: dict[ModelName, Classification]

    @property
    def classification(self) -> Classification:
        classifications = list(self.classifications.values())

        if len(classifications) != 1:
            raise MultiValueError(
                f"This document contains {len(classifications)} classifications. "
                "Use `document.classifications` instead."
            )

        return classifications[0]

    pre_review: PredictionList
    auto_review: PredictionList
    hitl_review: PredictionList
    post_review: PredictionList

    @staticmethod
    def from_result(result: dict[str, object]) -> "Document":
        """
        Factory function to produce a Document from a portion of a result file.
        """
        ...
