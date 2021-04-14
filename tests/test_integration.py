from solutions_toolkit.auto_review import ReviewConfiguration, Reviewer
from tests.conftest import MODEL_NAME


def test_submit_auto_review(workflow_wrapper, function_submission_ids):
    """
    Submit a document to a workflow, auto review the predictions, and retrieve the results
    """
    # Submit to workflow and get predictions
    result = workflow_wrapper.get_submission_result_from_id(function_submission_ids[0])
    predictions = result["results"]["document"]["results"][MODEL_NAME]["pre_review"]
    # Review the submission
    field_config = [
        {"function": "accept_by_confidence", "kwargs": {"conf_threshold": 0.99}},
        {
            "function": "reject_by_min_character_length",
            "kwargs": {
                "min_length_threshold": 3,
                "labels": ["Liability Amount", "Date of Appointment"],
            },
        },
    ]
    review_config = ReviewConfiguration(field_config)
    reviewer = Reviewer(predictions, review_config)
    reviewer.apply_reviews()
    # Submit the changes and retrieve reviewed results
    workflow_wrapper.submit_submission_review(
        function_submission_ids[0], {MODEL_NAME: reviewer.updated_predictions}
    )
    result = workflow_wrapper.get_submission_result_from_id(function_submission_ids[0])
    reviewed_preds = result["results"]["document"]["results"][MODEL_NAME]["final"]
    for pred in reviewed_preds:
        label = pred["label"]
        if (
            label in ["Liability Amount", "Date of Appointment"]
            and len(pred["text"]) < 3
        ):
            assert pred["rejected"] == True
        elif pred["confidence"][label] > 0.99:
            assert pred["accepted"] == True


