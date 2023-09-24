from dataclasses import dataclass
from typing import TypeAlias

from .errors import MultipleValuesError
from .spans import Span
from .utils import exists, get

Label: TypeAlias = str


@dataclass
class Prediction:
    model: str
    label: str
    confidences: dict[Label, float]

    @property
    def confidence(self) -> float:
        try:
            return self.confidences[self.label]
        except KeyError as key_error:
            raise AttributeError(
                "Prediction has no confidence for `{label!r}`."
            ) from key_error


@dataclass
class Classification(Prediction):
    @staticmethod
    def _from_v1_result(model: str, classification: object) -> "Classification":
        """
        Classify, Extract, and Classify+Extract Workflows.
        """
        return Classification(
            model=model,
            label=get(classification, "label", str),
            confidences=get(classification, "confidence", dict),
        )


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
        ...

    def reject(self) -> None:
        """
        Mark extraction as rejected for Auto Review.
        """
        ...

    @staticmethod
    def _from_v1_result(model: str, extraction: object) -> "Extraction":
        """
        Classify, Extract, and Classify+Extract Workflows.
        """
        if exists(extraction, "confidence", dict):
            # Pre-review extractions have confidence dicts.
            confidences = get(extraction, "confidence", dict)
        else:
            # Post-review extractions don't.
            confidences = {}

        return Extraction(
            model=model,
            label=get(extraction, "label", str),
            confidences=confidences,
            text=get(extraction, "text", str),
            spans=[Span._from_v1_result(extraction)],
        )

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
