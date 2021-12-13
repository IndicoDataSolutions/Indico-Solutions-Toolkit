import pytest
import tempfile
import pandas as pd
from indico_toolkit import ToolkitInputError
from indico_toolkit.indico_wrapper import Reviewer, Workflow
from indico_toolkit.indico_wrapper.workflow import COMPLETE_FILTER
from indico_toolkit.staggered_loop import StaggeredLoop
from indico_toolkit.types import WorkflowResult, Predictions, Extractions
from tests.indico_wrapper.test_reviewer import get_change_formatted_predictions


@pytest.fixture(scope="function")
def static_wflow_result():
    return WorkflowResult(
        dict(
            results=dict(
                document=dict(
                    results=dict(model_v1=dict(pre_review=[{}], final=[{}, {}]))
                )
            )
        )
    )


@pytest.fixture(scope="module")
def stagger_wrapper(indico_client):
    return StaggeredLoop(indico_client)


@pytest.fixture(scope="module")
def reviewed_submissions(workflow_id, indico_client, pdf_filepath):
    """
    Ensure that auto review is turned off and there are two "COMPLETE" human reviewed submissions
    """
    reviewer = Reviewer(indico_client, workflow_id)
    reviewer.update_workflow_settings(
        workflow_id, enable_review=True, enable_auto_review=False
    )
    sub_ids = reviewer.submit_documents_to_workflow(
        workflow_id, [pdf_filepath, pdf_filepath]
    )
    reviewer.wait_for_submissions_to_process(sub_ids)
    reviewed_ids = []
    for _ in range(2):
        id_in_review = reviewer.get_random_review_id()
        predictions = reviewer.get_submission_results_from_ids([id_in_review])
        changes = get_change_formatted_predictions(predictions[0])
        reviewer.accept_review(id_in_review, changes)
        reviewed_ids.append(id_in_review)
    reviewer.wait_for_submissions_to_process(reviewed_ids)
    return reviewed_ids


def test_get_reviewed_prediction_data(workflow_id, indico_client, reviewed_submissions):
    # num_submissions needed for now because of possible bug marking subs as retrieved for no reason
    wflow = Workflow(indico_client)
    num_submissions = len(
        wflow._get_list_of_submissions(
            workflow_id, COMPLETE_FILTER, reviewed_submissions
        )
    )
    stagger = StaggeredLoop(indico_client)
    stagger.get_reviewed_prediction_data(workflow_id, reviewed_submissions)
    assert len(stagger._filenames) == num_submissions
    assert len(stagger._workflow_results) == num_submissions
    assert len(stagger._snap_formatted_predictions) == num_submissions
    assert len(stagger._document_texts) == num_submissions
    for predictions in stagger._snap_formatted_predictions:
        assert isinstance(predictions, list)
        for pred in predictions:
            assert set(pred.keys()) == set(["label", "start", "end"])


def test_to_csv(stagger_wrapper, reviewed_submissions, workflow_id):
    with tempfile.NamedTemporaryFile(suffix=".csv") as tf:
        filepath = str(tf.name)
        stagger_wrapper.get_reviewed_prediction_data(workflow_id, reviewed_submissions)
        stagger_wrapper.to_csv(filepath)
        df = pd.read_csv(filepath)
        assert df.shape[0] > 0
        assert "text" in df.columns
        assert "target" in df.columns
        assert "filename" in df.columns


def test_convert_predictions_for_snapshot(stagger_wrapper):
    predictions = Predictions.get_obj(
        [
            {
                "text": "abc",
                "start": 1,
                "end": 4,
                "confidence": None,
                "label": "letters",
            },
            {
                "text": "def",
                "start": 4,
                "end": 7,
                "confidence": None,
                "label": "letters",
            },
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
    )
    stagger_wrapper.model_name = ""
    formatted_predictions = stagger_wrapper._reformat_predictions(predictions)
    assert len(formatted_predictions) == 2
    for pred in formatted_predictions:
        assert set(pred.keys()) == set(["label", "start", "end"])
        assert pred["label"] == "letters"


def test_get_nested_predictions(stagger_wrapper, static_wflow_result):
    stagger_wrapper.model_name = ""
    predictions = stagger_wrapper._get_nested_predictions(static_wflow_result)
    assert isinstance(predictions, Extractions)
    assert predictions.num_predictions == 2


def test_get_nested_predictions_bad_model_name(stagger_wrapper, static_wflow_result):
    stagger_wrapper.model_name = "Name doesn't exist"
    with pytest.raises(ToolkitInputError):
        stagger_wrapper._get_nested_predictions(static_wflow_result)


def test_get_nested_predictions_no_model_name(stagger_wrapper, static_wflow_result):
    stagger_wrapper.model_name = ""

    predictions = stagger_wrapper._get_nested_predictions(static_wflow_result)
    assert predictions.num_predictions == 2


def test_get_nested_predictions_no_model_name_fail(stagger_wrapper):
    wflow_result = WorkflowResult(
        dict(
            results=dict(
                document=dict(
                    results=dict(
                        model_v1=dict(pre_review=[{}], final=[{}, {}]),
                        model_v2=dict(pre_review=[{}], final=[{}, {}]),
                    )
                )
            )
        )
    )
    stagger_wrapper.model_name = ""
    with pytest.raises(ToolkitInputError):
        stagger_wrapper._get_nested_predictions(wflow_result)
