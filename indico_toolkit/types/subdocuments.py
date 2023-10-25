from dataclasses import dataclass

from .errors import MultipleValuesError
from .lists import ExtractionList, PredictionList
from .predictions import Classification, Prediction
from .spans import Span


@dataclass
class Subdocument(Prediction):
    classification: Classification
    extractions: ExtractionList
    spans: list[Span]

    @property
    def span(self) -> Span:
        if len(self.spans) != 1:
            raise MultipleValuesError(
                f"Subdocument has {len(self.spans)} spans. "
                "Use `Subdocument.spans` instead."
            )

        return self.spans[0]


class SubdocumentList(PredictionList[Subdocument]):
    pass
