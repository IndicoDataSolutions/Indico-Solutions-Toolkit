from dataclasses import dataclass
from functools import partial
from typing import TypeAlias

from .errors import MultipleValuesError
from .lists import ClassificationList, ExtractionList
from .predictions import Classification, Extraction
from .reviews import Review, ReviewType
from .utils import exists, get

Model: TypeAlias = str


@dataclass
class Subdocument:
    span_id: int
    classification: Classification
    final: ExtractionList


@dataclass
class Document:
    id: int
    filename: str
    etl_output: str
    classifications: ClassificationList
    pre_review: ExtractionList
    auto_review: ExtractionList
    hitl_review: ExtractionList
    final: ExtractionList
    subdocuments: list[Subdocument]

    @property
    def classification(self) -> Classification:
        if len(self.classifications) != 1:
            raise MultipleValuesError(
                f"Document has {len(self.classifications)} classifications. "
                "Use `Document.classifications` instead."
            )

        return self.classifications[0]

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
                    post_reviews_list, reviews, ReviewType.MANUAL
                )
                final_list = get(predictions_by_review, "final", list)

                extraction_for_model = partial(Extraction._from_v1_result, model)

                pre_review.extend(map(extraction_for_model, pre_review_list))
                auto_review.extend(map(extraction_for_model, auto_review_list))
                hitl_review.extend(map(extraction_for_model, hitl_review_list))
                final.extend(map(extraction_for_model, final_list))

        return Document(
            id=0,  # v1 sumissions do not have file IDs.
            filename="",  # v1 submissions do not include the original filename.
            etl_output=get(result, "etl_output", str),
            classifications=classifications,
            pre_review=pre_review,
            auto_review=auto_review,
            hitl_review=hitl_review,
            final=final,
            subdocuments=[],  # v1 submissions do not have unbundled subdocuments.
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

    @staticmethod
    def from_result(result: dict[str, object]) -> "Document":
        """
        Factory function to produce a Document from a portion of a result file.
        """
        if version == 1:
            pre_review, hitl_review, auto_review, final = Document.get_extractions_v1(
                result
            )
            classification, classifications = Document.get_classifications_v1(result)
        else:  # confirm if review supported for file versions 2 & 3, assuming not
            unbundle_models = {}
            extraction_models = {}
            classification_models = {}

            # TODO: not all models will have preds
            for modelgroup_id, metadata in result["modelgroup_metadata"].items():
                task_type = metadata["task_type"]
                if task_type == "classification_unbundling":
                    unbundle_models[modelgroup_id] = metadata["name"]
                elif task_type == "classification":
                    classification_models[modelgroup_id] = metadata["name"]
                elif task_type == "annotation":
                    extraction_models[modelgroup_id] = metadata["name"]

            all_models = {
                **unbundle_models,
                **extraction_models,
                **classification_models,
            }
            final = Document.get_extractions_v2_and_v3(result, all_models)
            classification, classifications = Document.get_classifications_v2_and_v3(
                result, classification_models
            )
            subdocuments = Document.get_subdocuments_v3(
                result, unbundle_models, all_models
            )

        return Document(
            id=id,
            filename=filename,
            etl_output=etl_output,
            classification=classification,
            classifications=classifications,
            subdocuments=subdocuments,
            pre_review=ExtractionList(pre_review),
            hitl_review=ExtractionList(hitl_review),
            auto_review=ExtractionList(auto_review),
            final=ExtractionList(final),
        )

    @staticmethod
    def get_extractions_v1(result_dict: dict):
        pre_review, hitl_review, auto_review, final = [], [], [], []
        model_results = result_dict["results"]["document"]["results"]
        review_active = "reviews_meta" in result_dict

        for model, results in model_results.items():
            if isinstance(results, list):
                final.extend(
                    Extraction.from_result(pred, model=model) for pred in results
                )
            elif isinstance(results, dict):
                if review_active:
                    if isinstance(
                        results["pre_review"], dict
                    ):  # classification, review
                        pre_review.append(
                            Extraction.from_result(results["pre_review"], model=model)
                        )
                        final.append(
                            Extraction.from_result(results["final"], model=model)
                        )
                    else:
                        pre_review.extend(
                            Extraction.from_result(pred, model=model)
                            for pred in results["pre_review"]
                        )
                        final.extend(
                            [
                                Extraction.from_result(pred, model=model)
                                for pred in results["final"]
                            ]
                        )
                        for i, post_review_preds in enumerate(results["post_reviews"]):
                            if (
                                result_dict["reviews_meta"][i]["review_type"]
                                == "manual"
                            ):
                                hitl_review.extend(
                                    [
                                        Extraction.from_result(pred, model=model)
                                        for pred in post_review_preds
                                    ]
                                )
                            elif (
                                result_dict["reviews_meta"][i]["review_type"] == "auto"
                            ):
                                auto_review.extend(
                                    [
                                        Extraction.from_result(pred, model=model)
                                        for pred in post_review_preds
                                    ]
                                )
                else:  # classification, no review
                    final.append(Extraction.from_result(results, model=model))
        return pre_review, hitl_review, auto_review, final

    @staticmethod
    def get_classifications_v1(result_dict: dict):
        classification = None
        classifications = {}
        classification_models = []
        review_active = "reviews_meta" in result_dict

        model_results = result_dict["results"]["document"]["results"]

        for model, results in model_results.items():
            if isinstance(results, dict) and (
                not review_active or isinstance(results["pre_review"], dict)
            ):
                classification_models.append(model)
                pred = results.get("final", results)
                classification_data = {
                    "model": model,
                    "label": pred["label"],
                    "confidence": pred["confidence"][pred["label"]],
                    "confidences": pred["confidence"],
                }
                if len(classification_models) == 1:
                    classification = Classification(**classification_data)
                else:
                    classifications[model] = Classification(**classification_data)

        return classification, classifications

    @staticmethod
    def get_extractions_v2_and_v3(result: dict, models: dict):
        final = []
        for model_id in models:
            final.extend(
                [
                    Extraction.from_result(pred, model=models[model_id])
                    for pred in result["model_results"]["ORIGINAL"][model_id]
                ]
            )
        return final

    @staticmethod
    def get_classifications_v2_and_v3(result: dict, classification_models: dict):
        classification = None
        classifications = {}
        if len(classification_models) == 1:
            model = next(iter(classification_models))
            pred = result["model_results"]["ORIGINAL"][model]
            classification = Classification(
                model=next(iter(classification_models.values())),
                label=pred["label"],
                confidence=pred["confidence"][pred["label"]],
                confidences=pred["confidence"],
            )
        elif len(classification_models) > 1:
            classifications = {}
            for model in classification_models:
                pred = result["model_results"]["ORIGINAL"][model]
                classifications[model] = Classification(
                    model=model,
                    label=pred["label"],
                    confidence=pred["confidence"][pred["label"]],
                    confidences=pred["confidence"],
                )
        return classification, classifications

    @staticmethod
    def get_subdocuments_v3(
        result: dict, unbundle_models: dict, extraction_models: dict
    ):
        unbundle_model = next(
            iter(unbundle_models)
        )  # for now assume one unbundle model
        unbundle_preds = result["model_results"]["ORIGINAL"][unbundle_model]
        subdocuments = []
        for unbundle_pred in unbundle_preds:
            span_id = unbundle_pred["span_id"]
            unbundle_label = unbundle_pred["label"]
            pages = [span["page_num"] for span in unbundle_pred["spans"]]
            classification = Classification(
                model=next(iter(unbundle_models.values())),
                label=unbundle_label,
                confidence=unbundle_pred["confidence"][unbundle_pred["label"]],
                confidences=unbundle_pred["confidence"],
            )
            final = []
            for extraction_model in extraction_models:
                extraction_preds = result["model_results"]["ORIGINAL"][extraction_model]
                for extraction_pred in extraction_preds:
                    for span in extraction_pred["spans"]:
                        if span["page_num"] in pages:
                            final.append(
                                Extraction.from_result(
                                    extraction_pred,
                                    model=extraction_models[extraction_model],
                                )
                            )
                            break
            subdocuments.append(
                Subdocument(
                    span_id=span_id,
                    classification=classification,
                    final=ExtractionList(final),
                )
            )
        return subdocuments
