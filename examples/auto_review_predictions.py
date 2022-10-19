"""
Submit documents to a workflow, auto review them and submit them for human review
"""
from indico_toolkit.auto_review import (
    ReviewConfiguration,
    AutoReviewer,
)
from indico_toolkit.indico_wrapper import Workflow
from indico_toolkit import create_client
from typing import List


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

# Make custom functions if needed
def reject_first_n_instances(predictions:List[dict], n_instances:int, labels:List[str])->List[dict]:
    """
        Custom autoreview function that rejects the first n predictions for a group of labels.
        Args:
            predictions(List[dict]): List of all predictions
            n_instances(int): Reject any predictions of a specific label before this number
            labels(List[str]): List of labels to apply this logic to
        Returns:
            An updated list of predictions with rejected logic added to preds that match function condition
    """
    for label in labels:
        matching_preds = [pred for pred in predictions if pred['label'] == label and "rejected" not in pred]
        for i, pred in enumerate(matching_preds):
            target_prediction = predictions[predictions.index(pred)]
            if i < n_instances:
                target_prediction["rejected"] = True
    return predictions
                

# Set up reviewer and review predictions
review_config = ReviewConfiguration(
    field_config=[
        {"function": "remove_by_confidence", "kwargs": {"conf_threshold": 0.90}},
        {
            "function": "accept_by_confidence",
            "kwargs": {"conf_threshold": 0.98, "labels": ["Name", "Amount"]},
        },
        {
            "function": "reject_after_n_instances",
            "kwargs": {"n_instances": 1, "labels": ["Name", "Amount"]},
        },
    ],
    custom_functions={
        "reject_after_n_instances": reject_first_n_instances
    }
)
auto_reviewer = AutoReviewer(predictions, review_config)
auto_reviewer.apply_reviews()

# Submit review
wflow.submit_submission_review(
    submission_ids[0], {MODEL_NAME: auto_reviewer.updated_predictions}
)

