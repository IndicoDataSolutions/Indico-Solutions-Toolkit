from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

from . import predictions as prediction
from .documents import Document
from .lists import PredictionList
from .models import ModelGroup
from .normalization import normalize_v1_result, normalize_v3_result
from .predictions import Prediction
from .reviews import Review, ReviewType
from .utils import get

if TYPE_CHECKING:
    from typing import Any


@dataclass(frozen=True, order=True)
class Result:
    version: int
    submission_id: int
    documents: "list[Document]"
    models: "list[ModelGroup]"
    predictions: "PredictionList[Prediction]"
    reviews: "list[Review]"

    @property
    def rejected(self) -> bool:
        return len(self.reviews) > 0 and self.reviews[-1].rejected

    @property
    def pre_review(self) -> "PredictionList[Prediction]":
        return self.predictions.where(review=None)

    @property
    def auto_review(self) -> "PredictionList[Prediction]":
        return self.predictions.where(review=ReviewType.AUTO)

    @property
    def manual_review(self) -> "PredictionList[Prediction]":
        return self.predictions.where(review=ReviewType.MANUAL)

    @property
    def admin_review(self) -> "PredictionList[Prediction]":
        return self.predictions.where(review=ReviewType.ADMIN)

    @property
    def final(self) -> "PredictionList[Prediction]":
        return self.predictions.where(review=self.reviews[-1] if self.reviews else None)

    @staticmethod
    def from_v1_dict(result: object) -> "Result":
        """
        Create a `Result` from a v1 result file dictionary.
        """
        normalize_v1_result(result)

        version = get(result, int, "file_version")
        submission_id = get(result, int, "submission_id")
        submission_results = get(result, dict, "results", "document", "results")
        review_metadata = get(result, list, "reviews_meta")

        document = Document.from_v1_dict(result)
        models = sorted(map(ModelGroup.from_v1_section, submission_results.items()))
        predictions: "PredictionList[Prediction]" = PredictionList()
        # Reviews must be sorted after parsing predictions, as they match positionally
        # with prediction lists in `post_reviews`.
        reviews = list(map(Review.from_dict, review_metadata))

        for model_name, model_predictions in submission_results.items():
            model = next(filter(lambda model: model.name == model_name, models))
            reviewed_model_predictions: "list[tuple[Review | None, Any]]" = [
                (None, get(model_predictions, list, "pre_review")),
                *filter(
                    lambda review_predictions: not review_predictions[0].rejected,
                    zip(reviews, get(model_predictions, list, "post_reviews")),
                ),
            ]

            for review, model_predictions in reviewed_model_predictions:
                predictions.extend(
                    map(
                        partial(prediction.from_v1_dict, document, model, review),
                        model_predictions,
                    )
                )

        return Result(
            version=version,
            submission_id=submission_id,
            documents=[document],
            models=models,
            predictions=predictions,
            reviews=sorted(reviews),
        )

    @staticmethod
    def from_v3_dict(result: object) -> "Result":
        """
        Create a `Result` from a v3 result file dictionary.
        """
        normalize_v3_result(result)

        version = get(result, int, "file_version")
        submission_id = get(result, int, "submission_id")
        submission_results = get(result, list, "submission_results")
        modelgroup_metadata = get(result, dict, "modelgroup_metadata")
        review_metadata = get(result, dict, "reviews")

        documents = sorted(map(Document.from_v3_dict, submission_results))
        models = sorted(map(ModelGroup.from_v3_dict, modelgroup_metadata.values()))
        predictions: "PredictionList[Prediction]" = PredictionList()
        reviews = sorted(map(Review.from_dict, review_metadata.values()))

        for document_dict in submission_results:
            document_id = get(document_dict, int, "submissionfile_id")
            document = next(
                filter(lambda document: document.id == document_id, documents)
            )
            reviewed_model_predictions: "list[tuple[Review | None, Any]]" = [
                (None, get(document_dict, dict, "model_results", "ORIGINAL"))
            ]

            if reviews:
                reviewed_model_predictions.append(
                    (reviews[-1], get(document_dict, dict, "model_results", "FINAL"))
                )

            for review, model_section in reviewed_model_predictions:
                for model_id, model_predictions in model_section.items():
                    model = next(
                        filter(lambda model: model.id == int(model_id), models)
                    )
                    predictions.extend(
                        map(
                            partial(prediction.from_v3_dict, document, model, review),
                            model_predictions,
                        )
                    )

        return Result(
            version=version,
            submission_id=submission_id,
            documents=documents,
            models=models,
            predictions=predictions,
            reviews=reviews,
        )
