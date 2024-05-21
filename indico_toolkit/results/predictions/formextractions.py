from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from ..reviews import Review
from ..utils import get, has, omit
from .autoreviewable import AutoReviewable

if TYPE_CHECKING:
    from typing import Any

    from ..documents import Document
    from ..models import ModelGroup


class FormExtractionType(StrEnum):
    CHECKBOX = "checkbox"
    SIGNATURE = "signature"
    TEXT = "text"


@dataclass
class FormExtraction(AutoReviewable):
    type: FormExtractionType
    checked: bool
    signed: bool
    text: str

    page: int
    top: int
    bottom: int
    left: int
    right: int

    @staticmethod
    def _from_dict(
        document: "Document",
        model: "ModelGroup",
        review: "Review | None",
        prediction: object,
    ) -> "FormExtraction":
        """
        Create a `FormExtraction` from a prediction dictionary.
        """
        return FormExtraction(
            document=document,
            model=model,
            review=review,
            label=get(prediction, str, "label"),
            confidences=get(prediction, dict, "confidence"),
            type=FormExtractionType(get(prediction, str, "type")),
            checked=(
                has(prediction, bool, "normalized", "structured", "checked")
                and get(prediction, bool, "normalized", "structured", "checked")
            ),
            signed=(
                has(prediction, bool, "normalized", "structured", "signed")
                and get(prediction, bool, "normalized", "structured", "signed")
            ),
            text=get(prediction, str, "normalized", "formatted"),
            page=get(prediction, int, "page_num"),
            top=get(prediction, int, "top"),
            bottom=get(prediction, int, "bottom"),
            left=get(prediction, int, "left"),
            right=get(prediction, int, "right"),
            accepted=(
                has(prediction, bool, "accepted") and get(prediction, bool, "accepted")
            ),
            rejected=(
                has(prediction, bool, "rejected") and get(prediction, bool, "rejected")
            ),
            extras=omit(
                prediction,
                "label",
                "confidence",
                "type",
                "checked",
                "signed",
                "page_num",
                "top",
                "bottom",
                "left",
                "right",
                "accepted",
                "rejected",
            ),
        )

    from_v1_dict = _from_dict
    from_v3_dict = _from_dict

    def _to_dict(self) -> "dict[str, Any]":
        """
        Create a prediction dictionary for auto review changes.
        """
        prediction = {
            **self.extras,
            "label": self.label,
            "confidence": self.confidences,
            "type": self.type,
            "page_num": self.page,
            "top": self.top,
            "bottom": self.bottom,
            "left": self.left,
            "right": self.right,
        }

        if self.type == FormExtractionType.CHECKBOX:
            prediction["normalized"]["structured"]["checked"] = self.checked
            prediction["normalized"]["formatted"] = (
                "Checked" if self.checked else "Unchecked"
            )
        elif self.type == FormExtractionType.SIGNATURE:
            prediction["normalized"]["structured"]["signed"] = self.signed
            prediction["normalized"]["formatted"] = (
                "Signed" if self.signed else "Unsigned"
            )
        elif self.type == FormExtractionType.TEXT:
            prediction["text"] = self.text
            prediction["normalized"]["formatted"] = self.text

        if self.accepted:
            prediction["accepted"] = True
        elif self.rejected:
            prediction["rejected"] = True

        return prediction

    to_v1_dict = _to_dict
    to_v3_dict = _to_dict
