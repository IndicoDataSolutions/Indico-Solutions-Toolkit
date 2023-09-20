from collections.abc import Callable

from .predictions import Prediction


class PredictionList(list[Prediction]):
    def where(
        self,
        *,
        model: str | None = None,
        label: str | None = None,
        min_confidence: float | None = None,
        max_confidence: float | None = None,
        predicate: Callable[[Prediction], bool] | None = None,
    ) -> "PredictionList":
        """
        Return a new `PredictionList` containing `Prediction`s
        that match the specified filters.
        """
        ...

    def apply(
        self,
        function: Callable[[Prediction], None],
    ) -> "PredictionList":
        """
        Apply a function to a list of predictions.
        """
        ...

    def accept(self) -> "PredictionList":
        """
        Mark predictions as accepted for Autoreview.
        """
        ...

    def reject(self) -> "PredictionList":
        """
        Mark predictions as rejected for Autoreview.
        """
        ...

    def to_changes(self) -> dict[str, object]:
        """
        Produce a dict structure suitable for `SubmitReview`.
        """
        ...
