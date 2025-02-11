"""
Overview of dataclasses and functionality available in the results module.
"""

from operator import attrgetter
from pathlib import Path

from indico import IndicoClient
from indico.queries import GetSubmission, RetrieveStorageObject

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
    result = results.load(result_file, reader=Path.read_text)


"""
Example Results Traversal
"""

# Get the classification of a single-document submission that went through a
# single-classification workflow.
result.pre_review.classifications[0].label

# Get the highest-confidence prediction for the Invoice Number field.
invoice_numbers = result.pre_review.extractions.where(label="Invoice Number")
invoice_number = invoice_numbers.orderby(attrgetter("confidence"), reverse=True)[0]
invoice_number.text

# Get all auto review predictions grouped by model.
predictions_by_model = result.auto_review.groupby(attrgetter("model"))

# Get all final extractions on page 5.
result.final.extractions.where(predicate=lambda pred: pred.page == 5)


"""
Dataclass Reference Summary

See class definitions for complete reference.
"""

# Result Dataclass
result.submission_id  # Submission ID
result.version  # Result file version
result.documents  # List of documents in this submission
result.models  # List of documents in this submission
result.reviews  # List of reviews for this submission
result.rejected  # Whether this submission was rejected in review

result.predictions  # List of all model predictions
result.pre_review  # List of raw model predictions
result.auto_review  # List of predictions for auto review
result.manual_review  # List of predictions for manual review
result.admin_review  # List of predictions for admin review
result.final  # List of final predictions


# Review Dataclass
if result.reviews:
    review = result.reviews[0]
    review.id
    review.reviewer_id
    review.notes
    review.rejected
    review.type


# Document Dataclass
document = result.documents[0]
document.id
document.name
document.etl_output_uri


# Prediction list Dataclass
predictions = result.final
predictions.classifications  # List of all classification predictions
predictions.extractions  # List of all document extraction predictions
predictions.form_extractions  # List of all form extraction predictions
predictions.unbundlings  # List of all unbundling predictions

predictions.apply()  # Apply a function to all predictions
predictions.groupby()  # Group predictions into a dictionary by some attribute (e.g. label)
predictions.orderby()  # Sort predictions by some attribute (e.g. confidence)
predictions.where()  # Filter predictions by some predicate (e.g. model, label, confidence)
predictions.to_changes(result)  # Get this list of predictions as changes for `SubmitReview`

predictions.extractions.accept()  # Accept all extractions in this list (e.g. after filtering)
predictions.extractions.reject()  # Reject all extractions in this list (e.g. after filtering)
predictions.extractions.unaccept()  # Unaccept all extractions in this list (e.g. after filtering)
predictions.extractions.unreject()  # Unreject all extractions in this list (e.g. after filtering)


# Prediction Dataclass
prediction = predictions[0]
prediction.document
prediction.model
prediction.label
prediction.confidence  # Confidence of the predicted label
prediction.confidences  # Confidences of all labels
prediction.extras  # Other attributes from the result file prediction dict that are not explicitly parsed


# Extraction Dataclass (Subclass of Prediction)
extraction = predictions.extractions[0]
extraction.text
extraction.page
extraction.accepted
extraction.rejected

extraction.accept()  # Mark this extraction as accepted for auto review
extraction.reject()  # Mark this extraction as rejected for auto review
extraction.unaccept()  # Mark this extraction as not accepted for auto review
extraction.unreject()  # Mark this extraction as not rejected for auto review


# DocumentExtraction Dataclass (Subclass of Extraction)
document_extraction = predictions.document_extractions[0]
document_extraction.text
document_extraction.span.page
document_extraction.span.start
document_extraction.span.end
document_extraction.groups  # Any linked label groups this prediction is a part of
document_extraction.accepted
document_extraction.rejected

document_extraction.accept()  # Mark this extraction as accepted for auto review
document_extraction.reject()  # Mark this extraction as rejected for auto review
document_extraction.unaccept()  # Mark this extraction as not accepted for auto review
document_extraction.unreject()  # Mark this extraction as not rejected for auto review


# FormExtraction Dataclass (Subclass of Extraction)
form_extraction = predictions.form_extractions[0]
form_extraction.type
form_extraction.text
form_extraction.checked
form_extraction.signed
form_extraction.box.page
form_extraction.box.top
form_extraction.box.left
form_extraction.box.right
form_extraction.box.bottom
form_extraction.accepted
form_extraction.rejected

form_extraction.accept()  # Mark this extraction as accepted for auto review
form_extraction.reject()  # Mark this extraction as rejected for auto review
form_extraction.unaccept()  # Mark this extraction as not accepted for auto review
form_extraction.unreject()  # Mark this extraction as not rejected for auto review
