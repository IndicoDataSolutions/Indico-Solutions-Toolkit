import pytest
from indico_toolkit.types import Predictions, WorkflowResult
from indico_toolkit import ToolkitInputError, ToolkitStatusError


def test_get_predictions_set_model_name(wf_result_obj):
    preds = wf_result_obj.predictions
    assert isinstance(preds, Predictions)
    assert isinstance(wf_result_obj.model_name, str)


def test_bad_model_name(wf_result_obj):
    wf_result_obj.model_name = "invalid model name"
    with pytest.raises(ToolkitInputError):
        wf_result_obj.predictions


def test_no_final_preds():
    wf_result = WorkflowResult(
        {"submission_id": 12, "results": {"document": {"results": {"model_v1": {"pre_review": []}}}}},
        "model_v1",
    )
    with pytest.raises(ToolkitStatusError):
        wf_result.post_review_predictions


def test_predictions_no_pre_review():
    wf_result = WorkflowResult({"results": {"document": {"results": []}}, "submission_id": 12}, "model_v1")
    assert isinstance(wf_result.predictions, Predictions)
