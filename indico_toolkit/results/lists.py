from collections import defaultdict
from typing import TYPE_CHECKING, List, TypeVar

from .errors import MultipleValuesError
from .predictions import Classification, Extraction, Prediction, Unbundling
from .utils import nfilter

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Self

PredictionType = TypeVar("PredictionType", bound=Prediction)
KeyType = TypeVar("KeyType")


class BaseList(List[PredictionType]):
    @property
    def labels(self) -> "set[str]":
        """
        Return unique prediction labels.
        """
        return set(prediction.label for prediction in self)

    @property
    def models(self) -> "set[str]":
        """
        Return unique prediction models.
        """
        return set(prediction.model for prediction in self)

    def apply(
        self,
        function: "Callable[[PredictionType], None]",
    ) -> "Self":
        """
        Apply a function to all predictions.
        """
        for prediction in self:
            function(prediction)

        return self

    def groupby(
        self,
        key: "Callable[[PredictionType], KeyType]",
    ) -> "dict[KeyType, Self]":
        """
        Group predictions into a dictionary using `key`.
        E.g. `key=attrgetter("label")` or `key=attrgetter("model")`
        """
        grouped = defaultdict(type(self))  # type: ignore[var-annotated]

        for prediction in self:
            grouped[key(prediction)].append(prediction)

        return grouped

    def orderby(
        self,
        key: "Callable[[PredictionType], bool]",
        *,
        reverse: bool = False,
    ) -> "Self":
        """
        Return a new prediction list with predictions sorted by `key`.
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
        model: "str | None" = None,
        label: "str | None" = None,
        min_confidence: "float | None" = None,
        max_confidence: "float | None" = None,
        predicate: "Callable[[PredictionType], bool] | None" = None,
    ) -> "Self":
        """
        Return a new prediction list containing predictions that match
        all of the specified filters.

        model: predictions from this model,
        label: predictions with this label,
        min_confidence: predictions with confidence >= this threshold,
        max_confidence: predictions with confidence <= this threshold,
        predicate: predictions for which this function returns True.
        """
        predicates = []

        if model is not None:
            predicates.append(lambda pred: pred.model == model)

        if label is not None:
            predicates.append(lambda pred: pred.label == label)

        if min_confidence is not None:
            predicates.append(lambda pred: pred.confidence >= min_confidence)

        if max_confidence is not None:
            predicates.append(lambda pred: pred.confidence <= max_confidence)

        if predicate is not None:
            predicates.append(predicate)

        return type(self)(nfilter(predicates, self))


class ClassificationList(BaseList[Classification]):
    def to_changes(self) -> "dict[str, object]":
        """
        Return a dict structure suitable for the `changes` argument of `SubmitReview`.
        """
        return {
            model: self.where(model=model)[0]._to_changes() for model in self.models
        }


class ExtractionList(BaseList[Extraction]):
    def accept(self) -> "ExtractionList":
        """
        Mark extractions as accepted for auto-review.
        """
        self.apply(lambda extraction: extraction.accept())
        return self

    def reject(self) -> "ExtractionList":
        """
        Mark extractions as rejected for auto-review.
        """
        self.apply(lambda extraction: extraction.reject())
        return self

    def to_changes(self) -> "dict[str, object]":
        """
        Return a dict structure suitable for the `changes` argument of `SubmitReview`.
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


class UnbundlingList(BaseList[Unbundling]):
    pass


class PredictionList(BaseList[Prediction]):
    @property
    def classification(self) -> Classification:
        """
        Shortcut to get the classification of a single classification model workflow.
        """
        classifications = self.classifications

        if len(classifications) != 1:
            raise MultipleValuesError(
                f"Prediction list has {len(classifications)} classifications. "
                "Use `PredictionList.classifications` instead."
            )

        return classifications[0]

    @property
    def classifications(self) -> ClassificationList:
        """
        Get classifications as a ClassificationList.
        """
        return ClassificationList(
            filter(
                lambda prediction: isinstance(prediction, Classification),  # type: ignore[arg-type]
                self,
            )
        )

    @property
    def extractions(self) -> ExtractionList:
        """
        Get extractions as a ExtractionList.
        """
        return ExtractionList(
            filter(
                lambda prediction: isinstance(prediction, Extraction),  # type: ignore[arg-type]
                self,
            )
        )

    @property
    def unbundlings(self) -> UnbundlingList:
        """
        Get unbundlings as a UnbundlingList.
        """
        return UnbundlingList(
            filter(
                lambda prediction: isinstance(prediction, Unbundling),  # type: ignore[arg-type]
                self,
            )
        )

    def to_changes(self) -> "dict[str, object]":
        """
        Return a dict structure suitable for the `changes` argument of `SubmitReview`.
        """
        return {
            **self.classifications.to_changes(),
            **self.extractions.to_changes(),
        }
