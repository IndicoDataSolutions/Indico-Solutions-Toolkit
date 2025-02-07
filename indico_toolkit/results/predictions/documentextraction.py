from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..review import Review
from ..utilities import get, has, omit
from .extraction import Extraction
from .group import Group
from .span import NULL_SPAN, Span

if TYPE_CHECKING:
    from typing import Any

    from ..document import Document
    from ..model import ModelGroup


@dataclass
class DocumentExtraction(Extraction):
    groups: "set[Group]"
    spans: "list[Span]"

    @property
    def span(self) -> Span:
        """
        Return the first `Span` the document extraction covers else `NULL_SPAN`.

        Post-review, document extractions have no spans.
        """
        return self.spans[0] if self.spans else NULL_SPAN

    @span.setter
    def span(self, span: Span) -> None:
        """
        Overwrite all `spans` with the one provided.

        This is implemented under the assumption that if you're setting the single span,
        you want it to be the only one. And if you're working in a context that's
        multiple-span sensetive, you'll set `extraction.spans` instead.
        """
        self.spans = [span]

    @staticmethod
    def from_v1_dict(
        document: "Document",
        model: "ModelGroup",
        review: "Review | None",
        prediction: object,
    ) -> "DocumentExtraction":
        """
        Create a `DocumentExtraction` from a v1 prediction dictionary.
        """
        return DocumentExtraction(
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
            groups=set(map(Group.from_dict, get(prediction, list, "groupings"))),
            spans=[Span.from_dict(prediction)] if has(prediction, int, "start") else [],
            extras=omit(
                prediction,
                "label",
                "confidence",
                "accepted",
                "rejected",
                "groupings",
                "page_num",
                "start",
                "end",
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
        Create a `DocumentExtraction` from a v3 prediction dictionary.
        """
        return DocumentExtraction(
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
            groups=set(map(Group.from_dict, get(prediction, list, "groupings"))),
            spans=sorted(map(Span.from_dict, get(prediction, list, "spans"))),
            extras=omit(
                prediction,
                "label",
                "confidence",
                "accepted",
                "rejected",
                "groupings",
                "spans",
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
            "groupings": [group.to_dict() for group in self.groups],
            "page_num": self.span.page,
            "start": self.span.start,
            "end": self.span.end,
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
            "spans": [span.to_dict() for span in self.spans],
        }

        prediction["normalized"]["formatted"] = self.text
        prediction["text"] = self.text  # 6.10 sometimes reverts to raw text in review.

        if self.accepted:
            prediction["accepted"] = True
        elif self.rejected:
            prediction["rejected"] = True

        return prediction
