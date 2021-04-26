import pytest
import json
from solutions_toolkit.staggered_loop import StaggeredLoop
from indico.queries import UpdateWorkflowSettings, GraphQLRequest

# TODO: move review queries in toolkit functionality or a conftest

SUBMIT_REVIEW = """
mutation submitStandardQueue($changes: JSONString, $rejected: Boolean, $submissionId: Int!, $notes: String) {
  submitReview(changes: $changes, rejected: $rejected, submissionId: $submissionId, notes: $notes) {
    id
    __typename
  }
}
"""

GET_RANDOM = """
query getSubmission($workflowId: Int!) {
  randomSubmission(adminReview: false, workflowId: $workflowId) {
    id
    resultFile
    inputFilename
    autoReview {
      id
      changes
      __typename
    }
    __typename
  }
}
"""

def accept_in_human_review(client, workflow_id, changes):
    response = client.call(
        GraphQLRequest(query=GET_RANDOM, variables={"workflowId": workflow_id})
    )

    submission_id = response["randomSubmission"]["id"]

    _ = client.call(
        GraphQLRequest(
            query=SUBMIT_REVIEW,
            variables={
                "rejected": False,
                "submissionId": submission_id,
                "changes": json.dumps(changes),
            },
        )
    )
    return submission_id


@pytest.fixture(scope="module")
def complete_submissions(workflow_id, workflow_wrapper, pdf_filepath):
    workflow_wrapper.indico_client.call(
            UpdateWorkflowSettings(
                workflow_id,
                enable_review=True,
                enable_auto_review=False,
            )
        )
    sub_ids = workflow_wrapper.submit_documents_to_workflow(workflow_id, [pdf_filepath])
    workflow_wrapper.wait_for_submissions_to_process(sub_ids)
    accept_in_human_review(workflow_wrapper.indico_client, workflow_id, {"Toolkit Test Financial Model": [{
                        "start": 225,
                        "end": 239,
                        "label": "Name",
                        "text": "Berkowitz, Avi",
                        "confidence": {
                            "Asset Value": 1.878555977441465e-08,
                        }
                    },]})
    return sub_ids


def test_get_reviewed_prediction_data(workflow_id, workflow_wrapper, complete_submissions):
    stagger = StaggeredLoop(workflow_id=workflow_id, submission_ids=complete_submissions)
    stagger.get_reviewed_prediction_data(workflow_wrapper)
    assert len(stagger._filenames) == 1
    assert len(stagger._workflow_results) == 1
    assert len(stagger._snap_formatted_predictions) == 1
    assert len(stagger._document_texts) == 1
    assert stagger._filenames[0] == "fin_disc.pdf"
    assert "confidence" not in stagger._snap_formatted_predictions[0]
    assert "start" in stagger._snap_formatted_predictions[0]


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
            document=dict(results=dict(
                model_v1=dict(pre_review=[{}], final=[{}, {}]),
                model_v2=dict(pre_review=[{}], final=[{}, {}]),
                    ))
        )
    )
    stagger = StaggeredLoop(312, model_name="")
    with pytest.raises(RuntimeError):
        stagger._get_nested_predictions(wflow_result)
