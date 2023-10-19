from collections.abc import Collection
from copy import deepcopy
from dataclasses import dataclass
from typing import TypeAlias

from .errors import MultipleValuesError, ResultFileError
from .spans import Span
from .utils import get

Label: TypeAlias = str


@dataclass
class Prediction:
    model: str
    label: str
    confidences: dict[Label, float]
    extras: dict[str, object]

    @property
    def confidence(self) -> float:
        try:
            return self.confidences[self.label]
        except KeyError as key_error:
            raise AttributeError(
                "Prediction has no confidence for `{label!r}`."
            ) from key_error

    @staticmethod
    def _extras_from_result(result: object, omit: Collection[str]) -> dict[str, object]:
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

    def _to_changes(self) -> dict[str, object]:
        """
        Produce a dict structure suitable for the `changes` argument of `SubmitReview`.
        """
        return {
            **deepcopy(self.extras),
            "label": self.label,
            "confidence": self.confidences,
        }


@dataclass
class Extraction(Prediction):
    text: str
    spans: list[Span]

    @property
    def span(self) -> Span:
        if len(self.spans) != 1:
            raise MultipleValuesError(
                f"Extraction has {len(self.spans)} spans. "
                "Use `Extraction.spans` instead."
            )

        return self.spans[0]

    def accept(self) -> None:
        """
        Mark extraction as accepted for Auto Review.
        """
        if "rejected" in self.extras:
            del self.extras["rejected"]

        self.extras["accepted"] = True

    @property
    def accepted(self) -> bool:
        return "accepted" in self.extras and bool(self.extras["accepted"])

    def reject(self) -> None:
        """
        Mark extraction as rejected for Auto Review.
        """
        if "accepted" in self.extras:
            del self.extras["accepted"]

        self.extras["rejected"] = True

    @property
    def rejected(self) -> bool:
        return "rejected" in self.extras and bool(self.extras["rejected"])

    @classmethod
    def _from_v1_result(cls, model: str, extraction: object) -> "Extraction":
        """
        Classify, Extract, and Classify+Extract Workflows.
        """
        try:
            confidences = get(extraction, "confidence", dict)
        except ResultFileError:
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
                    "pageNum",
                    "start",
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

    def _to_changes(self) -> dict[str, object]:
        """
        Produce a dict structure suitable for the `changes` argument of `SubmitReview`.
        """
        changes = {
            **deepcopy(self.extras),
            "label": self.label,
            "text": self.text,
        }

        if self.confidences:
            changes.update(
                {
                    "confidence": self.confidences,
                    "start": self.span.start,
                    "end": self.span.end,
                    "page_num": self.span.page,
                }
            )
        else:
            changes["pageNum"] = self.span.page

            if self.span.start:
                changes.update(
                    {
                        "start": self.span.start,
                        "end": self.span.end,
                    }
                )

        return changes

    @staticmethod
    def from_result(result: dict[str, object], model: str) -> "Extraction":
        """
        Factory function to produce a `Extraction` from a portion of a result file.
        """
        text = result.get("text")
        label = result["label"]
        confidence = result.get("confidence", {}).get(label)
        confidences = result.get("confidence", {})

        if "spans" in result:
            spans = result["spans"]
        else:
            spans = [
                {
                    "start": result.get("start"),
                    "end": result.get("end"),
                    "page_num": result.get("page_num"),
                }
            ]

        return Extraction(
            model=model,
            text=text,
            label=label,
            spans=spans,
            confidence=confidence,
            confidences=confidences,
        )
