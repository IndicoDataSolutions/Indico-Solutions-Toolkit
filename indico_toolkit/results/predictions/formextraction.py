from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from ..review import Review
from ..utilities import get, has, omit
from .box import Box
from .extraction import Extraction

if TYPE_CHECKING:
    from typing import Any

    from ..document import Document
    from ..model import ModelGroup


class FormExtractionType(Enum):
    CHECKBOX = "checkbox"
    SIGNATURE = "signature"
    TEXT = "text"


@dataclass
class FormExtraction(Extraction):
    type: FormExtractionType
    box: Box
    checked: bool
    signed: bool

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
            text=get(prediction, str, "normalized", "formatted"),
            accepted=(
                has(prediction, bool, "accepted") and get(prediction, bool, "accepted")
            ),
            rejected=(
                has(prediction, bool, "rejected") and get(prediction, bool, "rejected")
            ),
            type=FormExtractionType(get(prediction, str, "type")),
            box=Box.from_dict(prediction),
            checked=(
                has(prediction, bool, "normalized", "structured", "checked")
                and get(prediction, bool, "normalized", "structured", "checked")
            ),
            signed=(
                has(prediction, bool, "normalized", "structured", "signed")
                and get(prediction, bool, "normalized", "structured", "signed")
            ),
            extras=omit(
                prediction,
                "label",
                "confidence",
                "accepted",
                "rejected",
                "type",
                "page_num",
                "top",
                "left",
                "right",
                "bottom",
                "checked",
                "signed",
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
            "type": self.type.value,
            "page_num": self.box.page,
            "top": self.box.top,
            "left": self.box.left,
            "right": self.box.right,
            "bottom": self.box.bottom,
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
            prediction["normalized"]["formatted"] = self.text
            prediction["text"] = self.text  # 6.10 sometimes reverts to text in review.

        if self.accepted:
            prediction["accepted"] = True
        elif self.rejected:
            prediction["rejected"] = True

        return prediction

    to_v1_dict = _to_dict
    to_v3_dict = _to_dict
