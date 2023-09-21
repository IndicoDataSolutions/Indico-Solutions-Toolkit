from dataclasses import dataclass
from typing import TypeAlias

Label: TypeAlias = str


@dataclass
class Prediction:
    model: str
    text: str
    label: str
    confidences: dict[Label, float]

    @property
    def confidence(self) -> float:
        return self.confidences[self.label]

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
