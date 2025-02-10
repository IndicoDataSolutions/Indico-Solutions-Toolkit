import re
from typing import TYPE_CHECKING

from .utilities import get, has

if TYPE_CHECKING:
    from collections.abc import Iterator
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

            # Form Extractions added in review may lack bounding boxes.
            # Set values that will equal `NULL_BOX`.
            if "type" in prediction and "top" not in prediction:
                prediction["page_num"] = 0
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
    task_type_by_model_group_id = {
        model_group_id: model_group["task_type"]
        for model_group_id, model_group in result["modelgroup_metadata"].items()
    }
    predictions_with_task_type: "Iterator[tuple[Any, str]]" = (
        (prediction, task_type_by_model_group_id[model_group_id])
        for submission_result in get(result, list, "submission_results")
        for review_result in get(submission_result, dict, "model_results").values()
        for model_group_id, model_results in review_result.items()
        for prediction in model_results
    )

    for prediction, task_type in predictions_with_task_type:
        # Predictions added in review may lack a `confidence` section.
        if "confidence" not in prediction:
            prediction["confidence"] = {prediction["label"]: 0}

        # Document Extractions added in review may lack spans.
        if (
            task_type in ("annotation", "genai_annotation")
            and "spans" not in prediction
        ):
            prediction["spans"] = []

        # Form Extractions added in review may lack bounding boxes.
        # Set values that will equal `NULL_BOX`.
        if task_type == "form_extraction" and "top" not in prediction:
            prediction["page_num"] = 0
            prediction["top"] = 0
            prediction["left"] = 0
            prediction["right"] = 0
            prediction["bottom"] = 0

        # Prior to 6.11, some Extractions lack a `normalized` section after
        # review.
        if (
            task_type in ("annotation", "form_extraction", "genai_annotation")
            and "normalized" not in prediction
        ):
            prediction["normalized"] = {"formatted": prediction["text"]}

        # Document Extractions that didn't go through a linked labels
        # transformer lack a `groupings` section.
        if (
            task_type in ("annotation", "genai_annotation")
            and "groupings" not in prediction
        ):
            prediction["groupings"] = []

        # Summarizations may lack citations after review.
        if task_type == "summarization" and "citations" not in prediction:
            prediction["citations"] = []

    # Prior to 6.8, v3 result files don't include a `reviews` section.
    if not has(result, dict, "reviews"):
        result["reviews"] = {}

    # Review notes are `None` unless the reviewer enters a reason for rejection.
    for review_dict in get(result, dict, "reviews").values():
        if not has(review_dict, str, "review_notes"):
            review_dict["review_notes"] = ""

    # Prior to 7.0, v3 result files don't include an `errored_files` section.
    if not has(result, dict, "errored_files"):
        result["errored_files"] = {}

    # Prior to 7.X, errored files may lack filenames.
    for file in get(result, dict, "errored_files").values():
        if not has(file, str, "input_filename") and has(file, str, "reason"):
            match = re.search(r"file '([^']*)' with id", get(file, str, "reason"))
            file["input_filename"] = match.group(1) if match else ""
