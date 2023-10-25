from dataclasses import dataclass
from functools import partial
from typing import TypeAlias

from .errors import MultipleValuesError, ResultFileError
from .lists import ClassificationList, ExtractionList
from .modelgroups import ModelGroup, ModelType
from .predictions import Classification, Extraction
from .reviews import Review, ReviewType
from .subdocuments import Subdocument, SubdocumentList
from .utils import exists, get

Model: TypeAlias = str


@dataclass
class Document:
    id: int | None
    filename: str | None
    etl_output: str
    classifications: ClassificationList
    pre_review: ExtractionList
    auto_review: ExtractionList
    hitl_review: ExtractionList
    final: ExtractionList
    subdocuments: SubdocumentList

    @property
    def classification(self) -> Classification:
        if len(self.classifications) != 1:
            raise MultipleValuesError(
                f"Document has {len(self.classifications)} classifications. "
                "Use `Document.classifications` instead."
            )

        return self.classifications[0]

    @property
    def labels(self) -> set[str]:
        """
        Return the all of the labels for this document.
        """
        return (
            self.classifications.labels
            | self.pre_review.labels
            | self.auto_review.labels
            | self.hitl_review.labels
            | self.final.labels
            | self.subdocuments.labels
        )

    @property
    def models(self) -> set[str]:
        """
        Return the all of the models for this document.
        """
        return (
            self.classifications.models
            | self.pre_review.models
            | self.auto_review.models
            | self.hitl_review.models
            | self.final.models
            | self.subdocuments.models
        )

    @classmethod
    def _from_v1_result(cls, result: object, reviews: list[Review]) -> "Document":
        """
        Classify, Extract, and Classify+Extract Workflows.
        """
        results = get(result, "results", dict)
        document = get(results, "document", dict)
        results = get(document, "results", dict)

        classifications = ClassificationList()
        pre_review = ExtractionList()
        auto_review = ExtractionList()
        hitl_review = ExtractionList()
        final = ExtractionList()

        for model, predictions_by_review in results.items():
            if exists(predictions_by_review, "pre_review", dict):
                classification_dict = get(predictions_by_review, "pre_review", dict)
                classification = Classification._from_v1_result(
                    model, classification_dict
                )
                classifications.append(classification)
            elif exists(predictions_by_review, "pre_review", list):
                pre_review_list = get(predictions_by_review, "pre_review", list)
                post_reviews_list = get(predictions_by_review, "post_reviews", list)
                auto_review_list = cls._get_post_review_list(
                    post_reviews_list, reviews, ReviewType.AUTO
                )
                hitl_review_list = cls._get_post_review_list(
                    post_reviews_list, reviews, ReviewType.HITL
                )

                try:
                    final_list = get(predictions_by_review, "final", list)
                except ResultFileError:
                    # Rejected submissions do not have final predictions.
                    final_list = []

                extraction_for_model = partial(Extraction._from_v1_result, model)

                pre_review.extend(map(extraction_for_model, pre_review_list))
                auto_review.extend(map(extraction_for_model, auto_review_list))
                hitl_review.extend(map(extraction_for_model, hitl_review_list))
                final.extend(map(extraction_for_model, final_list))

        return Document(
            id=None,  # v1 sumissions do not have file IDs.
            filename=None,  # v1 submissions do not include the original filename.
            etl_output=get(result, "etl_output", str),
            classifications=classifications,
            pre_review=pre_review,
            auto_review=auto_review,
            hitl_review=hitl_review,
            final=final,
            subdocuments=SubdocumentList(),  # v1 submissions do not have unbundled subdocuments.
        )

    @staticmethod
    def _get_post_review_list(
        post_reviews_list: list[list[object]],
        reviews: list[Review],
        review_type: ReviewType,
    ) -> list[object]:
        """
        Return the `post_reviews` list that matches the first non-rejected review of the
        specified type, or an empty list if there are no matches.
        """
        for post_review_list, review in zip(post_reviews_list, reviews):
            if review.type == review_type and not review.rejected:
                return post_review_list
        else:
            return []

    @classmethod
    def _from_v2_result(
        cls, submission_result: object, model_groups_by_id: dict[int, ModelGroup]
    ) -> "Document":
        """
        Bundled Submission Workflows.
        """
        classifications = ClassificationList()
        extractions = ExtractionList()

        model_results = get(submission_result, "model_results", dict)
        original = get(model_results, "ORIGINAL", dict)

        for model_id_str, predictions_list in original.items():
            model_group = model_groups_by_id[int(model_id_str)]

            if model_group.type == ModelType.CLASSIFICATION:
                classifications.extend(
                    Classification._from_v2_result(model_group.name, prediction)
                    for prediction in predictions_list
                )
            elif model_group.type == ModelType.EXTRACTION:
                extractions.extend(
                    Extraction._from_v2_result(model_group.name, prediction)
                    for prediction in predictions_list
                )

        return Document(
            id=get(submission_result, "submissionfile_id", int),
            filename=get(submission_result, "input_filename", str),
            etl_output=get(submission_result, "etl_output", str),
            classifications=classifications,
            pre_review=extractions,
            auto_review=ExtractionList(),  # v2 submissions do not support review yet.
            hitl_review=ExtractionList(),  # v2 submissions do not support review yet.
            final=extractions,
            subdocuments=SubdocumentList(),  # v2 submissions do not have unbundled subdocuments.
        )

    @classmethod
    def _from_v3_result(
        cls, submission_result: object, model_groups_by_id: dict[int, ModelGroup]
    ) -> "Document":
        """
        Bundled Submission Workflows.
        """
        classifications = ClassificationList()
        extractions = ExtractionList()
        subdocuments = SubdocumentList()

        model_results = get(submission_result, "model_results", dict)
        original = get(model_results, "ORIGINAL", dict)

        for model_id_str, predictions_list in original.items():
            model_group = model_groups_by_id[int(model_id_str)]

            if model_group.type == ModelType.CLASSIFICATION:
                classifications.extend(
                    Classification._from_v3_result(model_group.name, prediction)
                    for prediction in predictions_list
                )
            elif model_group.type == ModelType.EXTRACTION:
                extractions.extend(
                    Extraction._from_v3_result(model_group.name, prediction)
                    for prediction in predictions_list
                )
            elif model_group.type == ModelType.UNBUNDLING:
                subdocuments.extend(
                    Subdocument._from_v3_result(model_group.name, prediction)
                    for prediction in predictions_list
                )

        for subdocument in subdocuments:
            pages = {span.page for span in subdocument.spans}
            subdocument.extractions = extractions.where(
                predicate=lambda extraction: any(
                    span.page in pages for span in extraction.spans
                )
            )

        return Document(
            id=get(submission_result, "submissionfile_id", int),
            filename=get(submission_result, "input_filename", str),
            etl_output=get(submission_result, "etl_output", str),
            classifications=classifications,
            pre_review=extractions,
            auto_review=ExtractionList(),  # v3 submissions do not support review yet.
            hitl_review=ExtractionList(),  # v3 submissions do not support review yet.
            final=extractions,
            subdocuments=subdocuments,
        )
