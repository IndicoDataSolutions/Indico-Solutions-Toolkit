from typing import TYPE_CHECKING

from .utils import get, has

if TYPE_CHECKING:
    from typing import Any


def normalize_v1_result(result: "Any") -> None:
    """
    Fix inconsistencies observed in v1 result files.
    """
    submission_results = get(result, dict, "results", "document", "results")

    # Incomplete and unreviewed submissions don't include a `reviews_meta` section.
    if not has(result, list, "reviews_meta"):
        result["reviews_meta"] = []

        for model_name, predictions in submission_results.items():
            submission_results[model_name] = {
                "pre_review": predictions,
                "post_reviews": [],
            }

    # Incomplete and unreviewed submissions retrieved with `SubmissionResult()` have a
    # single `{"review_id": None}` review.
    if not has(result, int, "reviews_meta", 0, "review_id"):
        result["reviews_meta"] = []

    # Review notes are `None` unless the reviewer enters a reason for rejection.
    for review_dict in get(result, list, "reviews_meta"):
        if not has(review_dict, str, "review_notes"):
            review_dict["review_notes"] = ""

    # Classifications aren't wrapped in lists like all other prediction types.
    for model_results in submission_results.values():
        if has(model_results, dict, "pre_review"):
            model_results["pre_review"] = [model_results["pre_review"]]
            model_results["post_reviews"] = [
                [prediction] for prediction in model_results["post_reviews"]
            ]


def normalize_v3_result(result: "Any") -> None:
    """
    Fix inconsistencies observed in v3 result files.
    """
    # Prior to 6.8, v3 result files don't include a `reviews` section.
    if not has(result, dict, "reviews"):
        result["reviews"] = {}

    # Review notes are `None` unless the reviewer enters a reason for rejection.
    for review_dict in get(result, dict, "reviews").values():
        if not has(review_dict, str, "review_notes"):
            review_dict["review_notes"] = ""
