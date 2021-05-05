import tempfile
import pandas as pd

from solutions_toolkit.types import Predictions


def test_init(static_preds):
    predictions = Predictions(predictions=static_preds)
    assert predictions.preds == static_preds
    assert isinstance(predictions.by_label["Name"], list)
    assert isinstance(predictions.by_label["Name"][0], dict)


def test_remove_by_confidence(predictions_obj):
    predictions_obj.remove_by_confidence(confidence=0.95, labels=["Name", "Department"])
    predictions_obj.remove_by_confidence(confidence=0.9)
    for pred in predictions_obj.preds:
        label = pred["label"]
        if label in ["Name", "Department"]:
            assert pred["confidence"][label] > 0.95
        else:
            assert pred["confidence"][label] > 0.9


def test_select_max_confidence(predictions_obj):
    predictions_obj.select_max_confidence(labels=["Name", "Department"])
    assert len(predictions_obj.by_label["Name"]) == 1
    assert len(predictions_obj.by_label["Department"]) == 1


def test_to_csv(predictions_obj):
    with tempfile.NamedTemporaryFile(suffix=".csv") as tf:
        filepath = str(tf.name)
        predictions_obj.to_csv(filepath)
        df = pd.read_csv(filepath)
        assert "text" in df.columns
        assert "end" in df.columns
        assert df.shape == (25, 5)


def test_by_label_to_csv(predictions_obj):
    with tempfile.NamedTemporaryFile(suffix=".csv") as tf:
        filepath = str(tf.name)
        predictions_obj.by_label_to_csv(filepath)
        df = pd.read_csv(filepath)
        assert "label_names" in df.columns
        assert "labels_list" in df.columns
        assert df.shape == (8, 2)

