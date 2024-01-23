from copy import deepcopy
from dataclasses import dataclass
from functools import reduce

from .documents import Document
from .errors import MultipleValuesError, ResultKeyError
from .modelgroups import ModelGroup
from .reviews import Review
from .utils import exists, get


@dataclass
class Submission:
    submission_id: int
    file_version: int
    documents: "list[Document]"
    reviews: "list[Review]"

    @property
    def bundled(self) -> bool:
        return len(self.documents) > 1

    @property
    def document(self) -> Document:
        """
        Shortcut to get the document of non-bundled submissions.
        """
        if self.bundled:
            raise MultipleValuesError(
                f"Submission has {len(self.documents)} documents. "
                "Use `Submission.documents` instead."
            )

        return self.documents[0]

    @property
    def labels(self) -> "set[str]":
        """
        Return unique prediction labels for all predictions for this submission.
        """
        return reduce(
            lambda labels, document: labels | document.labels,
            self.documents,
            set(),
        )

    @property
    def models(self) -> "set[str]":
        """
        Return unique prediction models for all predictions for this submission.
        """
        return reduce(
            lambda models, document: models | document.models,
            self.documents,
            set(),
        )

    @property
    def rejected(self) -> bool:
        return any(map(lambda review: review.rejected, self.reviews))

    @classmethod
    def from_result(cls, result: object) -> "Submission":
        """
        Factory function to produce a `Submission` from a result file dictionary.
        """
        file_version = get(result, "file_version", int)

        if file_version == 1:
            return cls._from_v1_result(result)
        elif file_version == 2:
            return cls._from_v2_result(result)
        elif file_version == 3:
            return cls._from_v3_result(result)
        else:
            raise ResultKeyError(f"Unknown file version `{file_version!r}`.")

    @classmethod
    def _from_v1_result(cls, result: object) -> "Submission":
        """
        Classify, Extract, and Classify+Extract Workflows.
        """
        if cls.is_unreviewed_result(result):
            raise ResultKeyError(
                "Result file has no review information. "
                "Use `SubmissionResult` to retrieve the result file "
                "or manually convert with `Submission.convert_to_reviewed_result`."
            )

        reviews_meta = get(result, "reviews_meta", list)

        # Unreviewed results retrieved through `SubmissionResult` have
        # { "reviews_meta": [{ "review_id": null }] }
        if reviews_meta and exists(reviews_meta[0], "review_id", int):
            reviews = list(map(Review._from_v1_result, reviews_meta))
        else:
            reviews = []

        return Submission(
            submission_id=get(result, "submission_id", int),
            file_version=1,
            documents=[Document._from_v1_result(result, reviews)],
            reviews=reviews,
        )

    @staticmethod
    def _from_v2_result(result: object) -> "Submission":
        """
        Bundled Submission Workflows.
        """
        modelgroup_metadata = get(result, "modelgroup_metadata", dict)
        model_groups = map(ModelGroup._from_v2_result, modelgroup_metadata.values())
        model_groups_by_id = {
            model_group.id: model_group for model_group in model_groups
        }

        return Submission(
            submission_id=get(result, "submission_id", int),
            file_version=2,
            documents=[
                Document._from_v2_result(submission_result, model_groups_by_id)
                for submission_result in get(result, "submission_results", list)
            ],
            reviews=[],  # Bundled submissions do not support review yet.
        )

    @staticmethod
    def _from_v3_result(result: object) -> "Submission":
        """
        Classify+Unbundle Workflows.
        """
        modelgroup_metadata = get(result, "modelgroup_metadata", dict)
        model_groups = map(ModelGroup._from_v3_result, modelgroup_metadata.values())
        model_groups_by_id = {
            model_group.id: model_group for model_group in model_groups
        }

        return Submission(
            submission_id=get(result, "submission_id", int),
            file_version=3,
            documents=[
                Document._from_v3_result(submission_result, model_groups_by_id)
                for submission_result in get(result, "submission_results", list)
            ],
            reviews=[],  # Unbundled submissions do not support review yet.
        )

    @staticmethod
    def is_unreviewed_result(result: object) -> bool:
        return (
            exists(result, "results", dict)
            and not exists(result, "reviews_meta", list)
        )  # fmt: skip

    @classmethod
    def convert_to_reviewed_result(cls, result: object) -> object:
        """
        Convert an unreviewed result file dictionary to a reviewed result file
        dictionary. Unreviewed result files don't have enough information to determine
        whether the contained predictions are pre-review, auto-review, manual-review,
        or admin-review; so only `Document.final` is populated.
        """
        result = deepcopy(result)

        results = get(result, "results", dict)
        document = get(results, "document", dict)
        results = get(document, "results", dict)

        for model, predictions in results.items():
            results[model] = {
                "pre_review": type(predictions)(),
                "post_reviews": [],
                "final": predictions,
            }

        result["reviews_meta"] = []  # type: ignore[index]

        return result
