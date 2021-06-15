import tempfile
import pandas as pd
from copy import deepcopy
from indico_toolkit.types import Extractions


def test_init(static_extract_preds):
    extractions = Extractions(static_extract_preds)
    assert extractions.to_list() == static_extract_preds
    assert isinstance(extractions["Name"], list)
    assert isinstance(extractions["Name"][0], dict)
    assert isinstance(extractions["Name"][0]["label"], str)


def test_remove_by_confidence(extractions_obj):
    extractions_obj.remove_by_confidence(confidence=0.95, labels=["Name", "Department"])
    extractions_obj.remove_by_confidence(confidence=0.9)
    for pred in extractions_obj.to_list():
        label = pred["label"]
        if label in ["Name", "Department"]:
            assert pred["confidence"][label] > 0.95
        else:
            assert pred["confidence"][label] > 0.9


def test_remove_except_max_confidence(extractions_obj):
    extractions_obj.remove_except_max_confidence(labels=["Name", "Department", "Not present label"])
    assert len(extractions_obj.to_dict_by_label["Name"]) == 1
    assert len(extractions_obj.to_dict_by_label["Department"]) == 1


def test_to_csv(extractions_obj):
    duplicated_obj = deepcopy(extractions_obj)
    with tempfile.NamedTemporaryFile(suffix=".csv") as tf:
        filepath = tf.name
        extractions_obj.to_csv(filepath, append_if_exists=False)
        df = pd.read_csv(filepath)
        assert "confidence" and "text" and "label" and "filename" in df.columns
        assert df.shape == (25, 4)
        duplicated_obj.to_csv(filepath, append_if_exists=True)
        df = pd.read_csv(filepath)
        assert df.shape == (50, 4)
