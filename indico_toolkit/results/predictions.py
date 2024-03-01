from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .errors import MultipleValuesError, ResultKeyError
from .spans import Span
from .utils import get

if TYPE_CHECKING:
    from collections.abc import Collection
    from typing import Any


@dataclass
class Prediction:
    model: str
    label: str
    confidences: "dict[str, float]"
    extras: "dict[str, Any]"

    @property
    def confidence(self) -> float:
        """
        Shortcut to get the confidence of the predicted label.
        """
        try:
            return self.confidences[self.label]
        except KeyError as key_error:
            raise AttributeError(
                "Prediction has no confidence for `{label!r}`."
            ) from key_error

    @staticmethod
    def _extras_from_result(
        result: object, omit: "Collection[str]"
    ) -> "dict[str, object]":
        if not isinstance(result, dict):
            return {}

        return {
            key: deepcopy(value) for key, value in result.items() if key not in omit
        }


@dataclass
class Classification(Prediction):
    @classmethod
    def _from_v1_result(cls, model: str, classification: object) -> "Classification":
        """
        Classify, Extract, and Classify+Extract Workflows.
        """
        return Classification(
            model=model,
            label=get(classification, "label", str),
            confidences=get(classification, "confidence", dict),
            extras=cls._extras_from_result(
                classification, omit=("confidence", "label")
            ),
        )

    @classmethod
    def _from_v2_result(cls, model: str, classification: object) -> "Classification":
        """
        Bundled Submission Workflows.
        """
        return cls._from_v1_result(model, classification)

    @classmethod
    def _from_v3_result(cls, model: str, classification: object) -> "Classification":
        """
        Classify+Unbundle Workflows.
        """
        return cls._from_v1_result(model, classification)

    def _to_changes(self) -> "dict[str, Any]":
        """
        Return a dict structure suitable for the `changes` argument of `SubmitReview`.
        """
        return {
            **deepcopy(self.extras),
            "label": self.label,
            "confidence": self.confidences,
        }


@dataclass
class Unbundling(Prediction):
    spans: "list[Span]"

    @property
    def span(self) -> Span:
        """
        Shortcut to get the span of unbundlings that don't have multiple spans.
        """
        if len(self.spans) != 1:
            raise MultipleValuesError(
                f"Unbundling has {len(self.spans)} spans. "
                "Use `Unbundling.spans` instead."
            )

        return self.spans[0]

    @classmethod
    def _from_v3_result(cls, model: str, unbundling: object) -> "Unbundling":
        """
        Classify+Unbundle Workflows.
        """
        return Unbundling(
            model=model,
            label=get(unbundling, "label", str),
            confidences=get(unbundling, "confidence", dict),
            spans=list(map(Span._from_v3_result, get(unbundling, "spans", list))),
            extras=cls._extras_from_result(
                unbundling, omit=("confidence", "label", "spans")
            ),
        )


@dataclass
class Extraction(Prediction):
    text: str
    spans: "list[Span]"

    @property
    def accepted(self) -> bool:
        return "accepted" in self.extras and bool(self.extras["accepted"])

    @property
    def rejected(self) -> bool:
        return "rejected" in self.extras and bool(self.extras["rejected"])

    @property
    def span(self) -> Span:
        """
        Shortcut to get the span of extractions that don't have multiple spans.
        """
        if len(self.spans) != 1:
            raise MultipleValuesError(
                f"Extraction has {len(self.spans)} spans. "
                "Use `Extraction.spans` instead."
            )

        return self.spans[0]

    def accept(self) -> None:
        """
        Mark extraction as accepted for auto-review.
        """
        self.unreject()
        self.extras["accepted"] = True

    def unaccept(self) -> None:
        """
        Mark extraction as not accepted for auto-review.
        """
        if "accepted" in self.extras:
            del self.extras["accepted"]

    def reject(self) -> None:
        """
        Mark extraction as rejected for auto-review.
        """
        self.unaccept()
        self.extras["rejected"] = True

    def unreject(self) -> None:
        """
        Mark extraction as not rejected for auto-review.
        """
        if "rejected" in self.extras:
            del self.extras["rejected"]

    @classmethod
    def _from_v1_result(cls, model: str, extraction: object) -> "Extraction":
        """
        Classify, Extract, and Classify+Extract Workflows.
        """
        try:
            confidences = get(extraction, "confidence", dict)
        except ResultKeyError:
            confidences = {}  # Post-review extractions don't have confidence dicts.

        return Extraction(
            model=model,
            label=get(extraction, "label", str),
            confidences=confidences,
            text=get(extraction, "text", str),
            spans=[Span._from_v1_result(extraction)],
            extras=cls._extras_from_result(
                extraction,
                omit=(
                    "confidence",
                    "end",
                    "label",
                    "page_num",
                    "pageNum",  # A platform bug causes manual-review extractions
                    "start",  #   to have a different key for page number.
                    "text",
                ),
            ),
        )

    @classmethod
    def _from_v2_result(cls, model: str, extraction: object) -> "Extraction":
        """
        Bundled Submission Workflows.
        """
        return Extraction(
            model=model,
            label=get(extraction, "label", str),
            confidences=get(extraction, "confidence", dict),
            text=get(extraction, "text", str),
            spans=[Span._from_v2_result(extraction)],
            extras=cls._extras_from_result(
                extraction,
                omit=(
                    "confidence",
                    "end",
                    "label",
                    "page_num",
                    "start",
                    "text",
                ),
            ),
        )

    @classmethod
    def _from_v3_result(cls, model: str, extraction: object) -> "Extraction":
        """
        Classify+Unbundle Workflows.
        """
        return Extraction(
            model=model,
            label=get(extraction, "label", str),
            confidences=get(extraction, "confidence", dict),
            text=get(extraction, "text", str),
            spans=list(map(Span._from_v3_result, get(extraction, "spans", list))),
            extras=cls._extras_from_result(
                extraction,
                omit=(
                    "confidence",
                    "label",
                    "spans",
                    "text",
                ),
            ),
        )

    def _to_changes(self) -> "dict[str, Any]":
        """
        Produce a dict structure suitable for the `changes` argument of `SubmitReview`.
        """
        changes = {
            **deepcopy(self.extras),
            "label": self.label,
            "page_num": self.span.page,
            "text": self.text,
        }

        # Post-review extractions don't have confidence dicts.
        if self.confidences:
            changes["confidence"] = self.confidences

        # Post-review extractions may not have start and end keys.
        if self.span.start:
            changes.update(
                {
                    "start": self.span.start,
                    "end": self.span.end,
                }
            )

        return changes
