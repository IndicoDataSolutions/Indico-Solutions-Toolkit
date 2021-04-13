import pytest
from solutions_toolkit.staggered_loop import StaggeredLoop


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
    formatted_predictions = stagger.convert_predictions_for_snapshot(predictions)
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
