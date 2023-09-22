from dataclasses import dataclass
from typing import TypeAlias

from .errors import MultipleValuesError
from .spans import Span

Label: TypeAlias = str


@dataclass
class Prediction:
    model: str
    field_id: int
    label: str
    confidences: dict[Label, float]

    @property
    def confidence(self) -> float:
        try:
            return self.confidences[self.label]
        except KeyError as key_error:
            raise AttributeError("This prediction has no confidences.") from key_error


@dataclass
class Classification(Prediction):
    @staticmethod
    def from_result(result: dict[str, object]) -> "Classification":
        """
        Factory function to produce a `Classification` from a portion of a result file.
        """
        ...


@dataclass
class Extraction(Prediction):
    text: str
    spans: list[Span]

    @property
    def span(self) -> Span:
        if len(self.spans) != 1:
            raise MultipleValuesError(
                f"This extraction contains {len(self.spans)} spans. "
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
