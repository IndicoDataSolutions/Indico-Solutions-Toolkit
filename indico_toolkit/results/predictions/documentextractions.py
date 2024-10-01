from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..reviews import Review
from ..utils import get, has, omit
from .extractions import Extraction
from .groups import Group

if TYPE_CHECKING:
    from typing import Any

    from ..documents import Document
    from ..models import ModelGroup


@dataclass
class DocumentExtraction(Extraction):
    page: int
    start: int
    end: int
    groups: "set[Group]"

    @staticmethod
    def from_v1_dict(
        document: "Document",
        model: "ModelGroup",
        review: "Review | None",
        prediction: object,
    ) -> "DocumentExtraction":
        """
        Create an `DocumentExtraction` from a v1 prediction dictionary.
        """
        return DocumentExtraction(
            document=document,
            model=model,
            review=review,
            label=get(prediction, str, "label"),
            confidences=get(prediction, dict, "confidence"),
            accepted=(
                has(prediction, bool, "accepted") and get(prediction, bool, "accepted")
            ),
            rejected=(
                has(prediction, bool, "rejected") and get(prediction, bool, "rejected")
            ),
            text=get(prediction, str, "normalized", "formatted"),
            page=get(prediction, int, "page_num"),
            start=get(prediction, int, "start"),
            end=get(prediction, int, "end"),
            groups=set(map(Group.from_dict, get(prediction, list, "groupings"))),
            extras=omit(
                prediction,
                "label",
                "confidence",
                "start",
                "end",
                "page_num",
                "groupings",
                "accepted",
                "rejected",
            ),
        )

    @staticmethod
    def from_v3_dict(
        document: "Document",
        model: "ModelGroup",
        review: "Review | None",
        prediction: object,
    ) -> "DocumentExtraction":
        """
        Create an `DocumentExtraction` from a v3 prediction dictionary.
        """
        return DocumentExtraction(
            document=document,
            model=model,
            review=review,
            label=get(prediction, str, "label"),
            confidences=get(prediction, dict, "confidence"),
            accepted=(
                has(prediction, bool, "accepted") and get(prediction, bool, "accepted")
            ),
            rejected=(
                has(prediction, bool, "rejected") and get(prediction, bool, "rejected")
            ),
            text=get(prediction, str, "normalized", "formatted"),
            page=get(prediction, int, "spans", 0, "page_num"),
            start=get(prediction, int, "spans", 0, "start"),
            end=get(prediction, int, "spans", 0, "end"),
            groups=set(map(Group.from_dict, get(prediction, list, "groupings"))),
            extras=omit(
                prediction,
                "label",
                "confidence",
                "groupings",
                "accepted",
                "rejected",
            ),
        )

    def to_v1_dict(self) -> "dict[str, Any]":
        """
        Create a prediction dictionary for v1 auto review changes.
        """
        prediction = {
            **self.extras,
            "label": self.label,
            "confidence": self.confidences,
            "page_num": self.page,
            "start": self.start,
            "end": self.end,
            "groupings": [group.to_dict() for group in self.groups],
        }

        prediction["normalized"]["formatted"] = self.text
        prediction["text"] = self.text  # 6.10 sometimes reverts to raw text in review.

        if self.accepted:
            prediction["accepted"] = True
        elif self.rejected:
            prediction["rejected"] = True

        return prediction

    def to_v3_dict(self) -> "dict[str, Any]":
        """
        Create a prediction dictionary for v3 auto review changes.
        """
        prediction = {
            **self.extras,
            "label": self.label,
            "confidence": self.confidences,
            "groupings": [group.to_dict() for group in self.groups],
        }

        prediction["normalized"]["formatted"] = self.text
        prediction["text"] = self.text  # 6.10 sometimes reverts to raw text in review.

        prediction["spans"][0]["page_num"] = self.page
        prediction["spans"][0]["start"] = self.start
        prediction["spans"][0]["end"] = self.end

        if self.accepted:
            prediction["accepted"] = True
        elif self.rejected:
            prediction["rejected"] = True

        return prediction
