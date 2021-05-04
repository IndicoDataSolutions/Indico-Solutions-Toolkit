import tempfile
import pandas as pd
import pytest
import json

from solutions_toolkit.types import Predictions
from tests.conftest import MODEL_NAME


@pytest.fixture(scope="session")
def static_preds():
    with open("tests/data/samples/fin_disc_result.json", "r") as infile:
        results = json.load(infile)
    return results["results"]["document"]["results"][MODEL_NAME]


@pytest.fixture(scope="function")
def predictions(static_preds):
    return Predictions(predictions=static_preds.copy())


def test_init(static_preds):
    predictions = Predictions(predictions=static_preds)
    assert predictions.preds == static_preds
    assert isinstance(predictions.by_label["Name"], list)
    assert isinstance(predictions.by_label["Name"][0], dict)


def test_remove_by_confidence(predictions):
    predictions.remove_by_confidence(confidence=0.95, labels=["Name", "Department"])
    predictions.remove_by_confidence(confidence=0.9)
    for pred in predictions.preds:
        label = pred["label"]
        if label in ["Name", "Department"]:
            assert pred["confidence"][label] > 0.95
        else:
            assert pred["confidence"][label] > 0.9


def test_select_max_confidence(predictions):
    predictions.select_max_confidence(labels=["Name", "Department"])
    assert len(predictions.by_label["Name"]) == 1
    assert len(predictions.by_label["Department"]) == 1


def test_to_csv(predictions):
    with tempfile.NamedTemporaryFile(suffix=".csv") as tf:
        filepath = str(tf.name)
        predictions.to_csv(filepath)
        df = pd.read_csv(filepath)
        assert "text" in df.columns
        assert "end" in df.columns
        assert df.shape == (25, 5)


def test_by_label_to_csv(predictions):
    with tempfile.NamedTemporaryFile(suffix=".csv") as tf:
        filepath = str(tf.name)
        predictions.by_label_to_csv(filepath)
        df = pd.read_csv(filepath)
        assert "label_names" in df.columns
        assert "labels_list" in df.columns
        assert df.shape == (8, 2)

