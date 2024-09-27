from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..reviews import Review
from ..utils import get, omit
from .predictions import Prediction

if TYPE_CHECKING:
    from typing import Any

    from ..documents import Document
    from ..models import ModelGroup


@dataclass
class Unbundling(Prediction):
    pages: "list[int]"

    @staticmethod
    def from_v3_dict(
        document: "Document",
        model: "ModelGroup",
        review: "Review | None",
        prediction: object,
    ) -> "Unbundling":
        """
        Create an `Unbundling` from a v3 prediction dictionary.
        """
        return Unbundling(
            document=document,
            model=model,
            review=review,
            label=get(prediction, str, "label"),
            confidences=get(prediction, dict, "confidence"),
            pages=[
                get(span, int, "page_num")
                for span in get(prediction, list, "spans")  # fmt: skip
            ],
            extras=omit(prediction, "confidence", "label", "spans"),
        )

    def to_v3_dict(self) -> "dict[str, Any]":
        """
        Create a prediction dictionary for v3 auto review changes.
        """
        return {
            **self.extras,
            "label": self.label,
            "confidence": self.confidences,
            "spans": [{"page_num": page} for page in self.pages],
        }
