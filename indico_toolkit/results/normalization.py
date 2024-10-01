from typing import TYPE_CHECKING

from .utils import get, has

if TYPE_CHECKING:
    from typing import Any


def normalize_v1_result(result: "Any") -> None:
    """
    Fix inconsistencies observed in v1 result files.
    """
    submission_results = get(result, dict, "results", "document", "results")

    for model_name, model_results in tuple(submission_results.items()):
        # Incomplete and unreviewed submissions don't have review sections.
        if not has(model_results, list, "post_reviews"):
            submission_results[model_name] = model_results = {
                "pre_review": model_results,
                "post_reviews": [],
            }

        # Classifications aren't wrapped in lists like other prediction types.
        if has(model_results, dict, "pre_review"):
            model_results["pre_review"] = [model_results["pre_review"]]
            model_results["post_reviews"] = [
                [prediction] for prediction in model_results["post_reviews"]
            ]

        predictions: "Any" = (
            prediction
            for review in (
                [get(model_results, list, "pre_review")]
                + get(model_results, list, "post_reviews")
            )
            if review is not None
            for prediction in review
            if prediction is not None
        )
        for prediction in predictions:
            # Predictions added in review lack a `confidence` section.
            if "confidence" not in prediction:
                prediction["confidence"] = {prediction["label"]: 0}

            # Document Extractions added in review may lack spans.
            if (
                "text" in prediction
                and "type" not in prediction
                and "start" not in prediction
            ):
                prediction["start"] = 0
                prediction["end"] = 0

            # Form Extractions added in review may lack bounding boxes.
            if "type" in prediction and "top" not in prediction:
                prediction["top"] = 0
                prediction["left"] = 0
                prediction["right"] = 0
                prediction["bottom"] = 0

            # Prior to 6.11, some Extractions lack a `normalized` section after review.
            if "text" in prediction and "normalized" not in prediction:
                prediction["normalized"] = {"formatted": prediction["text"]}

            # Document Extractions that didn't go through a linked labels transformer
            # lack a `groupings` section.
            if (
                "text" in prediction
                and "type" not in prediction
                and "groupings" not in prediction
            ):
                prediction["groupings"] = []

    # Incomplete and unreviewed submissions don't include a `reviews_meta` section.
    if not has(result, list, "reviews_meta"):
        result["reviews_meta"] = []

    # Incomplete and unreviewed submissions retrieved with `SubmissionResult()` have a
    # single `{"review_id": None}` review.
    if not has(result, int, "reviews_meta", 0, "review_id"):
        result["reviews_meta"] = []

    # Review notes are `None` unless the reviewer enters a reason for rejection.
    for review_dict in get(result, list, "reviews_meta"):
        if not has(review_dict, str, "review_notes"):
            review_dict["review_notes"] = ""


def normalize_v3_result(result: "Any") -> None:
    """
    Fix inconsistencies observed in v3 result files.
    """
    for document in get(result, list, "submission_results"):
        for review_results in get(document, dict, "model_results").values():
            predictions: "Any" = (
                prediction
                for model_results in review_results.values()
                for prediction in model_results
            )
            for prediction in predictions:
                # Predictions added in review lack a `confidence` section.
                if "confidence" not in prediction:
                    prediction["confidence"] = {prediction["label"]: 0}

                # Document Extractions added in review may lack spans.
                if (
                    "text" in prediction
                    and "type" not in prediction
                    and "spans" not in prediction
                ):
                    prediction["spans"] = [
                        {
                            "page_num": prediction["page_num"],
                            "start": 0,
                            "end": 0,
                        }
                    ]

                # Form Extractions added in review may lack bounding boxes.
                if "type" in prediction and "top" not in prediction:
                    prediction["top"] = 0
                    prediction["left"] = 0
                    prediction["right"] = 0
                    prediction["bottom"] = 0

                # Prior to 6.11, some Extractions lack a `normalized` section after
                # review.
                if "text" in prediction and "normalized" not in prediction:
                    prediction["normalized"] = {"formatted": prediction["text"]}

                # Document Extractions that didn't go through a linked labels
                # transformer lack a `groupings` section.
                if (
                    "text" in prediction
                    and "type" not in prediction
                    and "groupings" not in prediction
                ):
                    prediction["groupings"] = []

    # Prior to 6.8, v3 result files don't include a `reviews` section.
    if not has(result, dict, "reviews"):
        result["reviews"] = {}

    # Review notes are `None` unless the reviewer enters a reason for rejection.
    for review_dict in get(result, dict, "reviews").values():
        if not has(review_dict, str, "review_notes"):
            review_dict["review_notes"] = ""
