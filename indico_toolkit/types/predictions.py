from dataclasses import dataclass
from typing import TypeAlias

Label: TypeAlias = str


@dataclass
class Prediction:
    field_id: int
    model: str
    text: str
    label: str
    confidences: dict[Label, float]
    spans: list[Span]

    @property
    def confidence(self) -> float:
        return self.confidences[self.label]

    @property
    def span(self) -> Span:
        if len(self.spans) != 1:
            raise MultiValueError(
                f"This prediction contains {len(self.spans)} spans. "
                "Use `Prediction.spans` instead."
            )

        return self.spans[0]

    def accept(self) -> None:
        """
        Mark prediction as accepted for Autoreview.
        """
        ...

    def reject(self) -> None:
        """
        Mark prediction as rejected for Autoreview.
        """
        ...

    @staticmethod
    def from_result(result: dict[str, object]) -> "Prediction":
        """
        Factory function to produce a `Prediction` from a portion of a result file.
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

        return Prediction(
            model=model,
            text=text,
            label=label,
            spans=spans,
            confidence=confidence,
            confidences=confidences,
        )
