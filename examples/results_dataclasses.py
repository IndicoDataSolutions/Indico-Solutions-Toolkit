"""
Overview of dataclasses and functionality available in the results module.
"""
from operator import attrgetter
from pathlib import Path

from indico import IndicoClient
from indico.queries import GetSubmission, RetrieveStorageObject, SubmissionResult

from indico_toolkit import results

"""
Loading Result Files
"""

# Result files can be loaded as Python-native dataclasses from result dictionaries
# returned by the Indico client, from JSON strings, and from JSON files on disk.
client = IndicoClient()
submission = client.call(GetSubmission(123))
result_dict = client.call(RetrieveStorageObject(submission.result_file))
result = results.load(result_dict)

result = results.load("""{"file_version": 1, ... }""")

for result_file in Path("results_folder").glob("*.json"):
    result = results.load(result_file)


# Loading a result file uses the review information it contains to identify pre-review,
# auto-review, manual-review, admin-review, and final predictions. If your result file
# does not contain review information, loading it will raise an error. Use the
# `convert_unreviewed` argument to load the result file as if it were reviewed, using
# the predictions it contains as the final predictions.
result = results.load(result_dict, convert_unreviewed=True)


# If you're using the Indico client as a source, you may alternatively use
# `SubmissionResult` to include all review information currently available
# in the result file.
submission_result = client.call(SubmissionResult(submission, wait=True))
result_dict = client.call(RetrieveStorageObject(submission_result.result))
result = results.load(result_dict)


"""
Example Results Traversal
"""

# Get the classification of a single-document submission that went through a
# single-classification workflow.
result.document.pre_review.classification.label

# Get the highest-confidence prediction for the Invoice Number field.
invoice_numbers = result.document.pre_review.extractions.where(label="Invoice Number")
invoice_number = invoice_numbers.orderby(attrgetter("confidence"), reverse=True)[0]
invoice_number.text

# Get all auto review predictions grouped by model.
predictions_by_model = result.document.auto_review.groupby(attrgetter("model"))

# Get all final extractions on page 5.
result.document.final.extractions.where(predicate=lambda pred: pred.span.page == 5)


"""
Dataclass Reference
"""

# Result Dataclass
result.submission_id
result.file_version
result.bundled  # Is this submission bundled (contains multiple documents).
result.document  # Direct access to the single document in unbundled submissions.
result.documents  # List of documents in this submission.
result.reviews  # List of reviews for this submission.
result.rejected  # Whether this submission was rejected in review.


# Review Dataclass
if result.reviews:
    review = result.reviews[0]
    review.id
    review.reviewer_id
    review.notes
    review.rejected
    review.type  # Auto, manual, or admin review.


# Document Dataclass
document = (
    result.document
)  # Shorthand for `result.documents[0]` for single-document submissions.
document.file_id
document.filename
document.etl_output
document.pre_review  # List of raw model predictions.
document.auto_review  # List of predictions for this review.
document.manual_review  # List of predictions for this review.
document.admin_review  # List of predictions for this review.
document.final  # List of final predictions.


# Prediction list Dataclass
predictions = document.final
predictions.classification  # Shorthand for `predictions.classifications[0]` for single-classification workflows.
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
predictions.extractions.unaccept()  # Unaccept all extractions in this list (e.g. after filtering).
predictions.extractions.unreject()  # Unreject all extractions in this list (e.g. after filtering).


# Prediction Dataclass
prediction = predictions[0]
prediction.model
prediction.label
prediction.confidence  # Confidence of the predicted label.
prediction.confidences  # Confidences of all labels.
prediction.extras  # Other attributes from the result file prediction dict that are not explicitly parsed.


# Extraction Dataclass (Subclass of Prediction)
extraction.text
extraction.span  # Shorthand for `extraction.spans[0]` for single span extractions.
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


# Models & Labels
result.models  # Set of all models in the result.
result.labels  # Set of all labels in the result.
result.document.models  # Set of all models in the document.
result.document.labels  # Set of all labels in the document.
result.document.final.models  # Set of all models in final results (or pre-, auto-, manual-, and admin-review).
result.document.final.labels  # Set of all labels in final results (or pre-, auto-, manual-, and admin-review).
result.document.final.extractions.models  # Set of all models in final extractions (or any filtered or grouped list).
result.document.final.extractions.labels  # Set of all labels in final extractions (or any filtered or grouped list).
