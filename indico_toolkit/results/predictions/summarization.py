from dataclasses import dataclass
from typing import TYPE_CHECKING

from ..review import Review
from ..utilities import get, has, omit
from .citation import NULL_CITATION, Citation
from .extraction import Extraction

if TYPE_CHECKING:
    from typing import Any

    from ..document import Document
    from ..model import ModelGroup
    from .span import Span


@dataclass
class Summarization(Extraction):
    citations: "list[Citation]"

    @property
    def citation(self) -> Citation:
        """
        Return the first `Citation` the summarization covers else `NULL_CITATION`.

        Post-review, summarizations have no citations.
        """
        return self.citations[0] if self.citations else NULL_CITATION

    @citation.setter
    def citation(self, citation: Citation) -> None:
        """
        Overwrite all `citations` with the one provided.

        This is implemented under the assumption that if you're setting the single
        citation, you want it to be the only one. And if you're working in a context
        that's multiple-citation sensetive, you'll set `extraction.citations` instead.
        """
        self.citations = [citation]

    @property
    def span(self) -> "Span":
        return self.citation.span

    @span.setter
    def span(self, span: "Span") -> None:
        self.citations = [Citation(self.citation.start, self.citation.end, span)]

    @staticmethod
    def from_v3_dict(
        document: "Document",
        model: "ModelGroup",
        review: "Review | None",
        prediction: object,
    ) -> "Summarization":
        """
        Create a `Summarization` from a v3 prediction dictionary.
        """
        return Summarization(
            document=document,
            model=model,
            review=review,
            label=get(prediction, str, "label"),
            confidences=get(prediction, dict, "confidence"),
            text=get(prediction, str, "text"),
            accepted=(
                has(prediction, bool, "accepted") and get(prediction, bool, "accepted")
            ),
            rejected=(
                has(prediction, bool, "rejected") and get(prediction, bool, "rejected")
            ),
            citations=sorted(
                map(Citation.from_dict, get(prediction, list, "citations"))
            ),
            extras=omit(
                prediction,
                "label",
                "confidence",
                "text",
                "accepted",
                "rejected",
                "citations",
            ),
        )

    def to_v3_dict(self) -> "dict[str, Any]":
        """
        Create a prediction dictionary for v3 auto review changes.
        """
        prediction = {
            **self.extras,
            "label": self.label,
            "confidence": self.confidences,
            "text": self.text,
            "citations": [citation.to_dict() for citation in self.citations],
        }

        if self.accepted:
            prediction["accepted"] = True
        elif self.rejected:
            prediction["rejected"] = True

        return prediction
