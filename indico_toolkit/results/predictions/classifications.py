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
class Classification(Prediction):
    @staticmethod
    def _from_dict(
        document: "Document",
        model: "ModelGroup",
        review: "Review | None",
        prediction: object,
    ) -> "Classification":
        """
        Create a `Classification` from a prediction dictionary.
        """
        return Classification(
            document=document,
            model=model,
            review=review,
            label=get(prediction, str, "label"),
            confidences=get(prediction, dict, "confidence"),
            extras=omit(prediction, "label", "confidence"),
        )

    from_v1_dict = _from_dict
    from_v3_dict = _from_dict

    def _to_dict(self) -> "dict[str, Any]":
        """
        Create a prediction dictionary for auto review changes.
        """
        return {
            **self.extras,
            "label": self.label,
            "confidence": self.confidences,
        }

    to_v1_dict = _to_dict
    to_v3_dict = _to_dict
