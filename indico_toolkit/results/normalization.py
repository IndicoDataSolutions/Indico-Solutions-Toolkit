from typing import TYPE_CHECKING

from .utils import get, has

if TYPE_CHECKING:
    from typing import Any


def normalize_v1_result(result: "Any") -> None:
    """
    Fix inconsistencies observed in v1 result files.
    """
    submission_results = get(result, dict, "results", "document", "results")

    for model_name, predictions in tuple(submission_results.items()):
        # Incomplete and unreviewed submissions don't have review sections.
        if not has(predictions, list, "post_reviews"):
            submission_results[model_name] = predictions = {
                "pre_review": predictions,
                "post_reviews": [],
            }

        # Classifications aren't wrapped in lists like other prediction types.
        if has(predictions, dict, "pre_review"):
            predictions["pre_review"] = [predictions["pre_review"]]
            predictions["post_reviews"] = [
                [prediction] for prediction in predictions["post_reviews"]
            ]

        # Prior to 6.11, some predictions lack a `normalized` section after review.
        reviewed_predictions: "Any" = (
            prediction
            for review in get(predictions, list, "post_reviews")
            if review is not None
            for prediction in review
            if prediction is not None
        )
        for prediction in reviewed_predictions:
            if "text" in prediction and "normalized" not in prediction:
                prediction["normalized"] = {"formatted": prediction["text"]}

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
        # Prior to 6.11, some predictions lack a `normalized` section after review.
        if has(document, dict, "model_results", "FINAL"):
            reviewed_predictions: "Any" = (
                prediction
                for model in get(document, dict, "model_results", "FINAL")
                for prediction in model
            )
            for prediction in reviewed_predictions:
                if "text" in prediction and "normalized" not in prediction:
                    prediction["normalized"] = {"formatted": prediction["text"]}

    # Prior to 6.8, v3 result files don't include a `reviews` section.
    if not has(result, dict, "reviews"):
        result["reviews"] = {}

    # Review notes are `None` unless the reviewer enters a reason for rejection.
    for review_dict in get(result, dict, "reviews").values():
        if not has(review_dict, str, "review_notes"):
            review_dict["review_notes"] = ""
