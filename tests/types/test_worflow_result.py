import pytest


def test_get_predictions_set_model_name(wf_result_obj):
    preds = wf_result_obj.predictions
    assert isinstance(preds, list)
    assert isinstance(wf_result_obj.model_name, str)


def test_bad_model_name(wf_result_obj):
    wf_result_obj.model_name = "invalid model name"
    with pytest.raises(KeyError):
        _ = wf_result_obj.predictions
