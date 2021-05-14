import tempfile
import pandas as pd
from copy import deepcopy
from indico_toolkit.types import Predictions


def test_init(static_preds):
    predictions = Predictions(static_preds)
    assert predictions.to_list() == static_preds
    assert isinstance(predictions["Name"], list)
    assert isinstance(predictions["Name"][0], dict)
    assert isinstance(predictions["Name"][0]["label"], str)


def test_remove_by_confidence(predictions_obj):
    predictions_obj.remove_by_confidence(confidence=0.95, labels=["Name", "Department"])
    predictions_obj.remove_by_confidence(confidence=0.9)
    for pred in predictions_obj.to_list():
        label = pred["label"]
        if label in ["Name", "Department"]:
            assert pred["confidence"][label] > 0.95
        else:
            assert pred["confidence"][label] > 0.9


def test_remove_except_max_confidence(predictions_obj):
    predictions_obj.remove_except_max_confidence(labels=["Name", "Department"])
    assert len(predictions_obj.to_dict_by_label["Name"]) == 1
    assert len(predictions_obj.to_dict_by_label["Department"]) == 1


def test_to_csv(predictions_obj):
    duplicated_obj = deepcopy(predictions_obj)
    with tempfile.NamedTemporaryFile(suffix=".csv") as tf:
        filepath = str(tf.name)
        predictions_obj.to_csv(filepath, append_if_exists=False)
        df = pd.read_csv(filepath)
        assert "confidence" and "text" and "label" and "filename" in df.columns
        assert df.shape == (25, 4)
        duplicated_obj.to_csv(filepath, append_if_exists=True)
        df = pd.read_csv(filepath)
        assert df.shape == (50, 4)
