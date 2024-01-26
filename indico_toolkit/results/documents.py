from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

from .errors import ResultKeyError
from .lists import PredictionList
from .modelgroups import TaskType
from .predictions import Classification, Extraction, Unbundling
from .reviews import ReviewType
from .utils import exists, get

if TYPE_CHECKING:
    from .modelgroups import ModelGroup
    from .reviews import Review


@dataclass
class Document:
    file_id: "int | None"  # v1 sumissions do not have file IDs.
    filename: "str | None"  # v1 submissions do not include the original filename.
    etl_output_url: str
    pre_review: PredictionList
    auto_review: PredictionList
    manual_review: PredictionList
    admin_review: PredictionList
    final: PredictionList

    @property
    def labels(self) -> "set[str]":
        """
        Return unique prediction labels for all predictions for this document.
        """
        return (
            self.pre_review.labels
            | self.auto_review.labels
            | self.manual_review.labels
            | self.admin_review.labels
            | self.final.labels
        )

    @property
    def models(self) -> "set[str]":
        """
        Return unique prediction models for all predictions for this document.
        """
        return (
            self.pre_review.models
            | self.auto_review.models
            | self.manual_review.models
            | self.admin_review.models
            | self.final.models
        )

    @classmethod
    def _from_v1_result(cls, result: object, reviews: "list[Review]") -> "Document":
        """
        Classify, Extract, and Classify+Extract Workflows.
        """
        results = get(result, "results", dict)
        document = get(results, "document", dict)
        results = get(document, "results", dict)

        pre_review = PredictionList()
        auto_review = PredictionList()
        manual_review = PredictionList()
        admin_review = PredictionList()
        final = PredictionList()

        for model, predictions_by_review in results.items():
            # Check for classifications (dict types).
            # Pre-review won't be set for converted submissions.
            # Final won't be set for rejected submissions.
            if (
                exists(predictions_by_review, "pre_review", dict)
                or exists(predictions_by_review, "final", dict)
            ):  # fmt: skip
                pre_review_dict = get(predictions_by_review, "pre_review", dict)
                post_reviews_list = get(predictions_by_review, "post_reviews", list)
                auto_review_dict = cls._get_post_review_dict(
                    post_reviews_list, reviews, ReviewType.AUTO
                )
                manual_review_dict = cls._get_post_review_dict(
                    post_reviews_list, reviews, ReviewType.MANUAL
                )
                admin_review_dict = cls._get_post_review_dict(
                    post_reviews_list, reviews, ReviewType.ADMIN
                )

                try:
                    final_dict = get(predictions_by_review, "final", dict)
                except ResultKeyError:
                    # Rejected submissions don't have a `final` section.
                    final_dict = None

                classification_for_model = partial(
                    Classification._from_v1_result, model
                )

                if pre_review_dict:
                    pre_review.append(classification_for_model(pre_review_dict))
                if auto_review_dict:
                    auto_review.append(classification_for_model(auto_review_dict))
                if manual_review_dict:
                    manual_review.append(classification_for_model(manual_review_dict))
                if admin_review_dict:
                    admin_review.append(classification_for_model(admin_review_dict))
                if final_dict:
                    final.append(classification_for_model(final_dict))

            # Check for extractions (list types).
            elif exists(predictions_by_review, "pre_review", list):
                pre_review_list = get(predictions_by_review, "pre_review", list)
                post_reviews_list = get(predictions_by_review, "post_reviews", list)
                auto_review_list = cls._get_post_review_list(
                    post_reviews_list, reviews, ReviewType.AUTO
                )
                manual_review_list = cls._get_post_review_list(
                    post_reviews_list, reviews, ReviewType.MANUAL
                )
                admin_review_list = cls._get_post_review_list(
                    post_reviews_list, reviews, ReviewType.ADMIN
                )

                try:
                    final_list = get(predictions_by_review, "final", list)
                except ResultKeyError:
                    # Rejected submissions don't have a `final` section.
                    final_list = []

                extraction_for_model = partial(Extraction._from_v1_result, model)

                pre_review.extend(map(extraction_for_model, pre_review_list))
                auto_review.extend(map(extraction_for_model, auto_review_list))
                manual_review.extend(map(extraction_for_model, manual_review_list))
                admin_review.extend(map(extraction_for_model, admin_review_list))
                final.extend(map(extraction_for_model, final_list))

        return Document(
            file_id=None,  # v1 sumissions do not have file IDs.
            filename=None,  # v1 submissions do not include the original filename.
            etl_output_url=get(result, "etl_output", str),
            pre_review=pre_review,
            auto_review=auto_review,
            manual_review=manual_review,
            admin_review=admin_review,
            final=final,
        )

    @staticmethod
    def _get_post_review_dict(
        post_reviews_list: "list[dict[str, object]]",
        reviews: "list[Review]",
        review_type: ReviewType,
    ) -> "dict[str, object] | None":
        """
        Return the `post_reviews` dict that matches the first unrejected review of the
        specified type, or None if there are no matches. (Rejected reviews don't
        contain predictions.)
        """
        for post_review_dict, review in zip(post_reviews_list, reviews):
            if review.type == review_type and not review.rejected:
                return post_review_dict
        else:
            return None

    @staticmethod
    def _get_post_review_list(
        post_reviews_list: "list[list[object]]",
        reviews: "list[Review]",
        review_type: ReviewType,
    ) -> "list[object]":
        """
        Return the `post_reviews` list that matches the first unrejected review of the
        specified type, or an empty list if there are no matches. (Rejected reviews
        don't contain predictions.)
        """
        for post_review_list, review in zip(post_reviews_list, reviews):
            if review.type == review_type and not review.rejected:
                return post_review_list
        else:
            return []

    @classmethod
    def _from_v2_result(
        cls, submission_result: object, model_groups_by_id: "dict[int, ModelGroup]"
    ) -> "Document":
        """
        Bundled Submission Workflows.
        """
        predictions = PredictionList()
        model_results = get(submission_result, "model_results", dict)
        original = get(model_results, "ORIGINAL", dict)

        for model_id_str, predictions_list in original.items():
            model_group = model_groups_by_id[int(model_id_str)]

            if model_group.task_type == TaskType.CLASSIFICATION:
                predictions.extend(
                    Classification._from_v2_result(model_group.name, prediction)
                    for prediction in predictions_list
                )
            elif model_group.task_type == TaskType.EXTRACTION:
                predictions.extend(
                    Extraction._from_v2_result(model_group.name, prediction)
                    for prediction in predictions_list
                )

        return Document(
            file_id=get(submission_result, "submissionfile_id", int),
            filename=get(submission_result, "input_filename", str),
            etl_output_url=get(submission_result, "etl_output", str),
            pre_review=predictions,
            auto_review=PredictionList(),  # v2 submissions do not support review yet.
            manual_review=PredictionList(),  # v2 submissions do not support review yet.
            admin_review=PredictionList(),  # v2 submissions do not support review yet.
            final=predictions,
        )

    @classmethod
    def _from_v3_result(
        cls, submission_result: object, model_groups_by_id: "dict[int, ModelGroup]"
    ) -> "Document":
        """
        Bundled Submission Workflows.
        """
        predictions = PredictionList()
        model_results = get(submission_result, "model_results", dict)
        original = get(model_results, "ORIGINAL", dict)

        for model_id_str, predictions_list in original.items():
            model_group = model_groups_by_id[int(model_id_str)]

            if model_group.task_type == TaskType.CLASSIFICATION:
                predictions.extend(
                    Classification._from_v3_result(model_group.name, prediction)
                    for prediction in predictions_list
                )
            elif model_group.task_type == TaskType.EXTRACTION:
                predictions.extend(
                    Extraction._from_v3_result(model_group.name, prediction)
                    for prediction in predictions_list
                )
            elif model_group.task_type == TaskType.UNBUNDLING:
                predictions.extend(
                    Unbundling._from_v3_result(model_group.name, prediction)
                    for prediction in predictions_list
                )

        return Document(
            file_id=get(submission_result, "submissionfile_id", int),
            filename=get(submission_result, "input_filename", str),
            etl_output_url=get(submission_result, "etl_output", str),
            pre_review=predictions,
            auto_review=PredictionList(),  # v3 submissions do not support review yet.
            manual_review=PredictionList(),  # v3 submissions do not support review yet.
            admin_review=PredictionList(),  # v3 submissions do not support review yet.
            final=predictions,
        )
