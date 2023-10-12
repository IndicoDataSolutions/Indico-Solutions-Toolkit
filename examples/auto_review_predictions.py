"""
Submit documents to a workflow, auto review them and submit them for human review
"""
from indico_toolkit.auto_review import (
    AutoReviewFunction,
    AutoReviewer,
)
from indico_toolkit.auto_review.auto_review_functions import (
    remove_by_confidence,
    accept_by_confidence
)
from indico_toolkit.indico_wrapper import Workflow
from indico_toolkit import create_client


WORKFLOW_ID = 1234
HOST = "app.indico.io"
MODEL_NAME = "My_Model"
API_TOKEN_PATH = "./indico_api_token.txt"

# Instantiate the workflow class
client = create_client(HOST, API_TOKEN_PATH)
wflow = Workflow(client)

# Submit a document and get predictions
submission_ids = wflow.submit_documents_to_workflow(
    WORKFLOW_ID, pdf_filepaths=["./disclosures/disclosure_1.pdf"]
)
wf_results = wflow.get_submission_results_from_ids(submission_ids)
predictions = wf_results[0].predictions.to_list()

# Set up custom review function
def custom_function(predictions, labels: list = None, match_text: str = ""):
    for pred in predictions:
        if pred["text"] == match_text:
            pred["accepted"] = True
    return predictions


# Set up review functions and review predictions
functions = [
    AutoReviewFunction(remove_by_confidence, kwargs={"conf_threshold": 0.90}), # will default to all labels if labels is not provided
    AutoReviewFunction(accept_by_confidence, labels=["Name", "Amount"]),
    AutoReviewFunction(custom_function, kwargs={"match_text": "text to match"}) # call custom auto review function 
]
auto_reviewer = AutoReviewer(predictions, functions)
auto_reviewer.apply_reviews()

# Submit review
wflow.submit_submission_review(
    submission_ids[0], {MODEL_NAME: auto_reviewer.updated_predictions}
)

