import tempfile
import pandas as pd
from copy import deepcopy
import pytest
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
    extractions_obj.remove_except_max_confidence(
        labels=["Name", "Department", "Not present label"]
    )
    assert len(extractions_obj.to_dict_by_label["Name"]) == 1
    assert len(extractions_obj.to_dict_by_label["Department"]) == 1


def test_remove_keys(extractions_obj):
    keys_to_remove = ["start", "text"]
    extractions_obj.remove_keys(keys_to_remove)
    for pred in extractions_obj._preds:
        for key in keys_to_remove:
            assert key not in pred


def test_remove_keys_not_inplace(extractions_obj):
    keys_to_remove = ["start", "text"]
    preds = extractions_obj.remove_keys(keys_to_remove, inplace=False)
    for pred in preds:
        for key in keys_to_remove:
            assert key not in pred


def test_set_confidence_key_to_max_value(extractions_obj):
    extractions_obj.set_confidence_key_to_max_value()
    assert extractions_obj._preds[0]["confidence"] == 0.9999955296516418
    for pred in extractions_obj._preds:
        assert isinstance(pred["confidence"], float)


def test_set_confidence_key_to_max_value_not_inplace(extractions_obj):
    preds = extractions_obj.set_confidence_key_to_max_value(inplace=False)
    assert preds[0]["confidence"] == 0.9999955296516418
    for pred in preds:
        assert isinstance(pred["confidence"], float)


def test_to_csv(extractions_obj):
    duplicated_obj = deepcopy(extractions_obj)
    preds_copy = deepcopy(extractions_obj._preds)
    with tempfile.NamedTemporaryFile(suffix=".csv") as tf:
        filepath = tf.name
        extractions_obj.to_csv(filepath, append_if_exists=False)
        assert extractions_obj._preds == preds_copy
        df = pd.read_csv(filepath)
        assert "confidence" and "text" and "label" and "filename" in df.columns
        assert df.shape == (25, 4)
        duplicated_obj.to_csv(filepath, append_if_exists=True)
        df = pd.read_csv(filepath)
        assert df.shape == (50, 4)


@pytest.fixture(scope="function")
def test_extraction_preds():
    return [
        {"label": "Paydown Amount", "text": "a", "confidence": {"Paydown Amount": 0.8}},
        {"label": "Paydown Amount", "text": "b", "confidence": {"Paydown Amount": 0.9}},
        {"label": "Paydown Amount", "text": "c", "confidence": {"Paydown Amount": 0.7}},
        {
            "label": "Loan Amount",
            "text": "a",
            "confidence": {"Loan Amount": 0.99},
        },
        {
            "label": "Loan Amount",
            "text": "b",
            "confidence": {"Loan Amount": 0.99},
        },
    ]


def test_remove_all_by_label(test_extraction_preds):
    extract = Extractions(test_extraction_preds)
    extract._remove_all_by_label("Paydown Amount")
    assert len([i for i in extract.to_list() if i["label"] == "Paydown Amount"]) == 0


def test_remove_except_max_drop_and_ignore(test_extraction_preds):
    extract = Extractions(test_extraction_preds)
    extract.remove_except_max_confidence(labels=["Paydown Amount"])
    assert len(extract) == 3