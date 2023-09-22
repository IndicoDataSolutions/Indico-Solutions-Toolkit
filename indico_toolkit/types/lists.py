from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from typing import Self

from .predictions import Classification, Extraction, Prediction

PredictionType = TypeVar("PredictionType", bound=Prediction)


class PredictionList(list[PredictionType]):
    def where(
        self,
        *,
        model: str | None = None,
        label: str | None = None,
        min_confidence: float | None = None,
        max_confidence: float | None = None,
        predicate: Callable[[PredictionType], bool] | None = None,
    ) -> "Self":
        """
        Return a new `PredictionList[PredictionType]` containing `PredictionType`s
        that match the specified filters.
        """
        ...

    def apply(
        self,
        function: Callable[[PredictionType], None],
    ) -> "Self":
        """
        Apply a function to a list of predictions.
        """
        ...


class ClassificationList(PredictionList[Classification]):
    ...


class ExtractionList(PredictionList[Extraction]):
    def accept(self) -> "ExtractionList":
        """
        Mark predictions as accepted for Autoreview.
        """
        ...

    def reject(self) -> "ExtractionList":
        """
        Mark predictions as rejected for Autoreview.
        """
        ...

    def to_changes(self) -> dict[str, object]:
        """
        Produce a dict structure suitable for `SubmitReview`.
        """
        ...
