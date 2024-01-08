from collections import defaultdict
from collections.abc import Callable
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from typing import Self

from .predictions import Classification, Extraction, Prediction
from .utils import nfilter

PredictionType = TypeVar("PredictionType", bound=Prediction)
KeyType = TypeVar("KeyType")


class BaseList(list[PredictionType]):
    @property
    def labels(self) -> set[str]:
        """
        Return the all of the labels for these predictions.
        """
        return set(prediction.label for prediction in self)

    @property
    def models(self) -> set[str]:
        """
        Return the all of the models for these predictions.
        """
        return set(prediction.model for prediction in self)

    def apply(
        self,
        function: Callable[[PredictionType], None],
    ) -> "Self":
        """
        Apply a function to a list of predictions.
        """
        for prediction in self:
            function(prediction)

        return self

    def groupby(
        self,
        key: Callable[[PredictionType], KeyType],
    ) -> "dict[KeyType, Self]":
        """
        Return a dictionary of `PredictionList[PredictionType]` with `PredictionType`s
        grouped by `KeyType` using `key`.
        """
        grouped = defaultdict(type(self))  # type: ignore[var-annotated]

        for prediction in self:
            grouped[key(prediction)].append(prediction)

        return grouped

    def orderby(
        self,
        key: Callable[[PredictionType], bool],
        *,
        reverse: bool = False,
    ) -> "Self":
        """
        Return a new `PredictionList[PredictionType]` with `PredictionTypes`s
        sorted by `key`. Defaults to confidence ascending.
        """
        return type(self)(sorted(self, key=key, reverse=reverse))

    def sort(self, *args: object, **kwargs: object) -> None:
        raise RuntimeError(
            "PredictionLists should not be modified in place. "
            "Use `.orderby()` instead."
        )

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
        predicates = []

        if model is not None:
            predicates.append(lambda p: p.model == model)

        if label is not None:
            predicates.append(lambda p: p.label == label)

        if min_confidence is not None:
            predicates.append(lambda p: p.confidence >= min_confidence)

        if max_confidence is not None:
            predicates.append(lambda p: p.confidence <= max_confidence)

        if predicate is not None:
            predicates.append(predicate)

        return type(self)(nfilter(predicates, self))


class ClassificationList(BaseList[Classification]):
    def to_changes(self) -> dict[str, object]:
        """
        Produce a dict structure suitable for the `changes` argument of `SubmitReview`.
        """
        return {
            model: self.where(model=model)[0]._to_changes() for model in self.models
        }


class ExtractionList(BaseList[Extraction]):
    def accept(self) -> "ExtractionList":
        """
        Mark predictions as accepted for Autoreview.
        """
        self.apply(lambda e: e.accept())
        return self

    def reject(self) -> "ExtractionList":
        """
        Mark predictions as rejected for Autoreview.
        """
        self.apply(lambda e: e.reject())
        return self

    def to_changes(self) -> dict[str, object]:
        """
        Produce a dict structure suitable for the `changes` argument of `SubmitReview`.
        """
        return {
            model: list(
                map(
                    lambda extraction: extraction._to_changes(),
                    self.where(model=model),
                )
            )
            for model in self.models
        }


class PredictionList(BaseList[Prediction]):
    pass
