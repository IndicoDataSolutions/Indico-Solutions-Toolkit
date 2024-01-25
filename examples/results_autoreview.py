"""
Minimal auto review example for single-document submissions.
"""
from operator import attrgetter

from indico import IndicoClient
from indico.filters import SubmissionFilter
from indico.queries import ListSubmissions, RetrieveStorageObject, SubmitReview

from indico_toolkit import results


def autoreview(result: results.Result) -> dict[str, object]:
    """
    Apply simple auto review rules to a submission.
    Assumes single-document submissions.
    """
    pre_review = result.document.pre_review
    extractions = pre_review.extractions

    # Downselect all labels from all models based on highest confidence.
    for model, extractions in extractions.groupby(attrgetter("model")).items():
        for label, extractions in extractions.groupby(attrgetter("label")).items():
            # Order extractions by confidence descending.
            ordered = extractions.orderby(attrgetter("confidence"), reverse=True)
            ordered.reject()  # Reject all extractions.
            ordered[0].unreject()  # Unreject the highest confidence extraction.

    confidence_thresholds = {
        "From": 0.99,
        "To": 0.97,
        "Subject": 0.90,
        "Date": 0.99999,
    }

    # Auto accept predictions based on label's confidence threshold.
    for label, threshold in confidence_thresholds.items():
        extractions.where(label=label, min_confidence=threshold).accept()

    # Reject all predictions with confidence below 75%.
    extractions.where(max_confidence=0.75).reject()

    # Apply name normalization to all predictions with the "Name" label.
    extractions.where(label="Name").apply(normalize_name)

    return pre_review.to_changes()


def normalize_name(extraction: results.Extraction) -> None:
    """
    Normalize 'Last, First' to 'First Last'.
    """
    names = extraction.text.split(",")

    if len(names) == 2:
        last, first = names
        extraction.text = first.strip() + " " + last.strip()


if __name__ == "__main__":
    client = IndicoClient()

    for submission in client.call(
        ListSubmissions(
            workflow_ids=[123],
            filters=SubmissionFilter(status="PENDING_AUTO_REVIEW"),
        )
    ):
        result_dict = client.call(RetrieveStorageObject(submission.result_file))
        result = results.load(result_dict, convert_unreviewed=True)
        changes = autoreview(result)
        client.call(SubmitReview(submission.id, changes))
