"""
Working with result files using Python-native dataclasses.
"""
from collections.abc import Iterator
from operator import attrgetter
from pathlib import Path

import pendulum
import polars as pl

from indico import IndicoClient
from indico.queries import (
    GetSubmission,
    SubmissionResult,
    RetrieveStorageObject,
    SubmitReview,
)
from indico_toolkit import results


"""
Load a result file.
"""
client = IndicoClient()
submission = client.call(GetSubmission(123))  # Or similar.
result_dict = client.call(RetrieveStorageObject(submission.result_file))
result = results.load(result_dict)

# If your submission is unreviewed,
# generate a result file to include review information.
submission_result = client.call(SubmissionResult(submission, wait=True))
result_dict = client.call(RetrieveStorageObject(submission_result.result))
result = results.load(result_dict)

# Or convert the unreviewed submission to a reviewed submission.
# Due to the lack of review data, only `document.final` is populated.
result = results.load(result_dict, convert_unreviewed=True)

# `results.load` also takes JSON strings and file paths.
for result_file in Path("results_folder").glob("*.json"):
    result = results.load(result_file)


"""
Save document classification and extractions to CSV.
"""


def get_predictions(result: results.Result) -> Iterator[dict[str, object]]:
    yield {
        "submission_id": result.submission_id,
        "field": "Classification",
        "value": result.document.final.classification.label,
        "confidence": result.document.final.classification.confidence,
    }

    for extraction in result.document.final.extractions:
        yield {
            "submission_id": result.submission_id,
            "field": extraction.label,
            "value": extraction.text,
            "confidence": extraction.confidence,
        }


pl.DataFrame(get_predictions(result)).write_csv("predictions.csv")


"""
Auto review predictions.
"""
pre_review = result.document.pre_review
extractions = pre_review.extractions

# Downselect based on highest confidence.
for model, extractions in extractions.groupby(attrgetter("model")).items():
    for label, extractions in extractions.groupby(attrgetter("label")).items():
        extractions.reject()  # Reject all.
        extractions.orderby(attrgetter("confidence"), reverse=True)[
            0
        ].unreject()  # Unreject highest confidence.

# Auto accept and reject based on confidence.
thresholds = {
    "From": 0.99,
    "To": 0.97,
    "Subject": 0.90,
    "Date": 0.99999,
}

for label, threshold in thresholds.items():
    extractions.where(label=label, min_confidence=threshold).accept()

extractions.where(max_confidence=0.75).reject()


# Apply date normalization.
def normalize_date(extraction: results.Extraction) -> None:
    try:
        extraction.text = pendulum.parse(extraction.text).to_date_string()
    except Exception:
        pass


extractions.where(predicate=lambda e: "Date" in e.label).apply(normalize_date)

# Submit auto reviewed predictions.
client.call(SubmitReview(result.submission_id, changes=pre_review.to_changes()))


"""
Result object reference.
"""
result.submission_id
result.file_version
result.bundled  # Is this submission bundled (contains multiple documents).
result.document  # Direct access to the single document in unbundled submissions.
result.documents  # List of documents in this submission.
result.reviews  # List of reviews for this submission.
result.rejected  # Whether this submission was rejected in review.


"""
Review object reference.
"""
if result.reviews:
    review = result.reviews[0]
    review.id
    review.reviewer_id
    review.notes
    review.rejected
    review.type  # Auto, manual, or admin review.


"""
Document object reference.
"""
document = result.document
document.file_id
document.filename
document.etl_output
document.pre_review  # List of raw model predictions.
document.auto_review  # List of predictions for this review.
document.manual_review  # List of predictions for this review.
document.admin_review  # List of predictions for this review.
document.final  # List of final predictions.


"""
Prediction list object reference.
"""
predictions = document.final
predictions.classification  # Direct access to the single classification of a one-classification model workflow.
predictions.classifications  # List of all classification predictions.
predictions.extractions  # List of all extraction predictions.
predictions.unbundlings  # List of all unbundling predictions.

predictions.apply()  # Apply a function to all predictions.
predictions.groupby()  # Group predictions into a dictionary by some attribute (e.g. label).
predictions.orderby()  # Sort predictions by some attribute (e.g. confidence).
predictions.where()  # Filter predictions by some predicate (e.g. model, label, confidence).
predictions.to_changes()  # Get this list of predictions as a dictionary of changes for `SubmitReview`.

predictions.extractions.accept()  # Accept all extractions in this list (e.g. after filtering).
predictions.extractions.reject()  # Reject all extractions in this list (e.g. after filtering).


"""
Prediction object reference.
"""
prediction = predictions[0]
prediction.model
prediction.label
prediction.confidence  # Confidence of the predicted label.
prediction.confidences  # Confidences of all labels.
prediction.extras  # Other attributes from the prediction dict.

extraction.text
extraction.span  # Direct access for single span extractions.
extraction.span.start
extraction.span.end
extraction.span.page
extraction.spans  # List of spans for this extraction.
extraction.accepted
extraction.rejected
extraction.accept()  # Mark this extraction as accepted for auto review.
extraction.reject()  # Mark this extraction as rejected for auto review.
extraction.unaccept()  # Mark this extraction as not accepted for auto review.
extraction.unreject()  # Mark this extraction as not rejected for auto review.


"""
Models & labels reference.
"""
result.models  # Set of all models in the result.
result.labels  # Set of all labels in the result.
result.document.models  # Set of all models in the document.
result.document.labels  # Set of all labels in the document.
result.document.final.models  # Set of all models in final results (or pre-, auto-, manual-, and admin-review).
result.document.final.labels  # Set of all labels in final results (or pre-, auto-, manual-, and admin-review).
result.document.final.extractions.models  # Set of all models in final extractions (or any filtered or grouped list).
result.document.final.extractions.labels  # Set of all labels in final extractions (or any filtered or grouped list).
