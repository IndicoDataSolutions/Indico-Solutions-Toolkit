import pytest
import json
import time
from solutions_toolkit.indico_wrapper.workflow import COMPLETE_FILTER
from solutions_toolkit.staggered_loop import StaggeredLoop
from tests.indico_wrapper.test_reviewer import get_change_formatted_predictions
from indico.queries import UpdateWorkflowSettings, GraphQLRequest, GetSubmission


@pytest.fixture(scope="module")
def reviewed_submissions(workflow_id, workflow_wrapper, pdf_filepath, reviewer_wrapper):
    """
    Ensure that auto review is turned off and there are two "COMPLETE" human reviewed submissions
    """
    workflow_wrapper.update_workflow_settings(
        workflow_id, enable_review=True, enable_auto_review=False
    )
    sub_ids = workflow_wrapper.submit_documents_to_workflow(
        workflow_id, [pdf_filepath, pdf_filepath]
    )
    workflow_wrapper.wait_for_submissions_to_process(sub_ids)
    reviewed_ids = []
    for _ in range(2):
        id_in_review = reviewer_wrapper.get_random_review_id()
        predictions = reviewer_wrapper.get_submission_results_from_ids([id_in_review])
        changes = get_change_formatted_predictions(predictions)
        reviewer_wrapper.accept_review(id_in_review, changes)
        reviewed_ids.append(id_in_review)
    for sub_id in reviewed_ids:
        workflow_wrapper.wait_for_submission_status_complete(sub_id)
    # time.sleep(2) # provide buffer for DB to update
    print(reviewed_ids)
    return reviewed_ids


def test_get_reviewed_prediction_data(
    workflow_id, workflow_wrapper, reviewed_submissions
):
    # num_submissions needed for now because of possible bug marking subs as retrieved for no reason
    num_submissions = len(
        workflow_wrapper._get_list_of_submissions(
            workflow_id, COMPLETE_FILTER, reviewed_submissions
        )
    )
    stagger = StaggeredLoop(
        workflow_id=workflow_id, submission_ids=reviewed_submissions
    )
    stagger.get_reviewed_prediction_data(workflow_wrapper)
    assert len(stagger._filenames) == num_submissions
    assert len(stagger._workflow_results) == num_submissions
    assert len(stagger._snap_formatted_predictions) == num_submissions
    assert len(stagger._document_texts) == num_submissions
    for predictions in stagger._snap_formatted_predictions:
        assert isinstance(predictions, list)
        for pred in predictions:
            assert set(pred.keys()) == set(["label", "start", "end"])


def test_convert_predictions_for_snapshot():
    predictions = [
        {"text": "abc", "start": 1, "end": 4, "confidence": None, "label": "letters"},
        {"text": "def", "start": 4, "end": 7, "confidence": None, "label": "letters"},
        {
            "text": "shouldbeignored",
            "start": 0,
            "end": 0,
            "confidence": None,
            "label": "manuallyadded",
        },
        {
            "text": "shouldbeignored",
            "start": None,
            "end": None,
            "confidence": None,
            "label": "manuallyadded",
        },
    ]
    stagger = StaggeredLoop(312)
    formatted_predictions = stagger._reformat_predictions(predictions)
    assert len(formatted_predictions) == 2
    for pred in formatted_predictions:
        assert set(pred.keys()) == set(["label", "start", "end"])
        assert pred["label"] == "letters"


def test_get_nested_predictions():
    wflow_result = dict(
        results=dict(
            document=dict(results=dict(model_v1=dict(pre_review=[{}], final=[{}, {}])))
        )
    )
    stagger = StaggeredLoop(312, model_name="model_v1")
    predictions = stagger._get_nested_predictions(wflow_result)
    assert isinstance(predictions, list)
    assert len(predictions) == 2


def test_get_nested_predictions_bad_model_name():
    wflow_result = dict(
        results=dict(
            document=dict(results=dict(model_v1=dict(pre_review=[{}], final=[{}, {}])))
        )
    )
    stagger = StaggeredLoop(312, model_name="name_doesnt_exist")
    with pytest.raises(KeyError):
        stagger._get_nested_predictions(wflow_result)


def test_get_nested_predictions_no_model_name():
    wflow_result = dict(
        results=dict(
            document=dict(results=dict(model_v1=dict(pre_review=[{}], final=[{}, {}])))
        )
    )
    stagger = StaggeredLoop(312, model_name="")
    predictions = stagger._get_nested_predictions(wflow_result)
    assert len(predictions) == 2


def test_get_nested_predictions_no_model_name_fail():
    wflow_result = dict(
        results=dict(
            document=dict(
                results=dict(
                    model_v1=dict(pre_review=[{}], final=[{}, {}]),
                    model_v2=dict(pre_review=[{}], final=[{}, {}]),
                )
            )
        )
    )
    stagger = StaggeredLoop(312, model_name="")
    with pytest.raises(RuntimeError):
        stagger._get_nested_predictions(wflow_result)
