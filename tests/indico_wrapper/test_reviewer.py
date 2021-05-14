import pytest
from indico_toolkit.indico_wrapper import Reviewer, Workflow
from indico.queries import GetSubmission


@pytest.fixture(scope="module")
def submissions_awaiting_review(workflow_id, indico_client, pdf_filepath):
    """
    Ensure that auto review is turned off and there are two submissions "PENDING_REVIEW"
    """
    workflow_wrapper = Workflow(indico_client)
    workflow_wrapper.update_workflow_settings(
        workflow_id, enable_review=True, enable_auto_review=False
    )
    sub_ids = workflow_wrapper.submit_documents_to_workflow(
        workflow_id, [pdf_filepath, pdf_filepath]
    )
    workflow_wrapper.wait_for_submissions_to_process(sub_ids)


def get_change_formatted_predictions(workflow_result):
    """
    Helper function for get change format for accepted predictions in test_accept_review
    """
    return {workflow_result.model_name: workflow_result.predictions.to_list()}


def test_accept_review(submissions_awaiting_review, indico_client, workflow_id):
    reviewer_wrapper = Reviewer(indico_client, workflow_id)
    id_in_review = reviewer_wrapper.get_random_review_id()
    submission = reviewer_wrapper.get_submission_object(id_in_review)
    assert submission.status == "PENDING_REVIEW"
    predictions = reviewer_wrapper.get_submission_results_from_ids([id_in_review])
    changes = get_change_formatted_predictions(predictions[0])
    reviewer_wrapper.accept_review(id_in_review, changes)
    submission = reviewer_wrapper.get_submission_object(id_in_review)
    assert submission.status == "COMPLETE"


@pytest.mark.dependency()
def test_reject_from_review(submissions_awaiting_review, indico_client, workflow_id):
    reviewer_wrapper = Reviewer(indico_client, workflow_id)
    id_in_review = reviewer_wrapper.get_random_review_id()
    reviewer_wrapper.reject_submission(id_in_review)
    submission = reviewer_wrapper.get_submission_object(id_in_review)
    assert submission.status == "PENDING_ADMIN_REVIEW"


@pytest.mark.dependency(depends=["test_reject_from_review"])
def test_reject_from_admin_review(
    submissions_awaiting_review, indico_client, workflow_id
):
    reviewer_wrapper = Reviewer(indico_client, workflow_id)
    id_in_exception = reviewer_wrapper.get_random_exception_id()
    submission = reviewer_wrapper.get_submission_object(id_in_exception)
    assert submission.status == "PENDING_ADMIN_REVIEW"
    reviewer_wrapper.reject_submission(id_in_exception)
    submission = reviewer_wrapper.get_submission_object(id_in_exception)
    assert submission.status == "COMPLETE"
