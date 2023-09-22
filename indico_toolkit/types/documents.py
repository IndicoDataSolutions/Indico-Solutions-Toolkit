from dataclasses import dataclass
from typing import TypeAlias

from .classifications import Classification
from .errors import MultipleValuesError, ResultFileError
from .lists import PredictionList

Model: TypeAlias = str


@dataclass
class Subdocument:
    span_id: int
    classification: Classification
    final: PredictionList


@dataclass
class Document:
    id: int
    filename: str
    etl_output: str
    classifications: dict[Model, Classification]
    pre_review: PredictionList
    auto_review: PredictionList
    hitl_review: PredictionList
    final: PredictionList
    subdocuments: list[Subdocument]

    @property
    def classification(self) -> Classification:
        classifications = list(self.classifications.values())

        if len(classifications) != 1:
            raise MultipleValuesError(
                f"This document contains {len(classifications)} classifications. "
                "Use `Document.classifications` instead."
            )

        return classifications[0]

    @staticmethod
    def from_result(result: dict[str, object]) -> "Document":
        """
        Factory function to produce a Document from a portion of a result file.
        """
        id = result.get("submissionfile_id", result.get("submission_id"))
        filename = result.get("input_filename")
        etl_output = result.get("etl_output")

        # if review not activated in workflow, only populate "final" key
        pre_review, hitl_review, auto_review, final, subdocuments = [], [], [], [], []
        version = result.get("file_version")

        if version == 1:
            pre_review, hitl_review, auto_review, final = Document.get_predictions_v1(
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
            final = Document.get_predictions_v2_and_v3(result, all_models)
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
            pre_review=PredictionList(pre_review),
            hitl_review=PredictionList(hitl_review),
            auto_review=PredictionList(auto_review),
            final=PredictionList(final),
        )

    @staticmethod
    def get_predictions_v1(result_dict: dict):
        pre_review, hitl_review, auto_review, final = [], [], [], []
        model_results = result_dict["results"]["document"]["results"]
        review_active = "reviews_meta" in result_dict

        for model, results in model_results.items():
            if isinstance(results, list):
                final.extend(
                    Prediction.from_result(pred, model=model) for pred in results
                )
            elif isinstance(results, dict):
                if review_active:
                    if isinstance(
                        results["pre_review"], dict
                    ):  # classification, review
                        pre_review.append(
                            Prediction.from_result(results["pre_review"], model=model)
                        )
                        final.append(
                            Prediction.from_result(results["final"], model=model)
                        )
                    else:
                        pre_review.extend(
                            Prediction.from_result(pred, model=model)
                            for pred in results["pre_review"]
                        )
                        final.extend(
                            [
                                Prediction.from_result(pred, model=model)
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
                                        Prediction.from_result(pred, model=model)
                                        for pred in post_review_preds
                                    ]
                                )
                            elif (
                                result_dict["reviews_meta"][i]["review_type"] == "auto"
                            ):
                                auto_review.extend(
                                    [
                                        Prediction.from_result(pred, model=model)
                                        for pred in post_review_preds
                                    ]
                                )
                else:  # classification, no review
                    final.append(Prediction.from_result(results, model=model))
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
    def get_predictions_v2_and_v3(result: dict, models: dict):
        final = []
        for model_id in models:
            final.extend(
                [
                    Prediction.from_result(pred, model=models[model_id])
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
                                Prediction.from_result(
                                    extraction_pred,
                                    model=extraction_models[extraction_model],
                                )
                            )
                            break
            subdocuments.append(
                Subdocument(
                    span_id=span_id,
                    classification=classification,
                    final=PredictionList(final),
                )
            )
        return subdocuments
