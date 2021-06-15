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