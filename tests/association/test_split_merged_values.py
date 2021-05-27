import pytest
from indico_toolkit.association import split_prediction_into_many


def test_split_prediction_into_many_three_splits():
    test_case = {"text": "a\nb\n\nc", "start": 10, "end": 16, "confidence": None, "label": "test"}
    split_predictions = split_prediction_into_many(test_case, "\n")
    assert len(split_predictions) == 3
    assert split_predictions[0]["text"] == "a"
    assert split_predictions[0]["start"] == test_case["start"]
    assert split_predictions[0]["end"] == test_case["start"] + 1
    assert split_predictions[-1]["text"] == "c"
    assert split_predictions[-1]["start"] == 15
    assert split_predictions[-1]["end"] == 16


def test_split_prediction_into_many_no_splits():
    test_case = {"text": "no line breaks", "start": 5, "end": 19, "confidence": None, "label": "test"}
    split_predictions = split_prediction_into_many(test_case, "\n")
    assert len(split_predictions) == 1
    assert split_predictions[0]["text"] == "no line breaks"
    assert split_predictions[0]["start"] == 5
    assert split_predictions[0]["end"] == 19


def test_split_prediction_into_many_duplicate_test():
    test_case = {"text": "a\n\n a", "start": 5, "end": 10, "confidence": None, "label": "test"}
    split_predictions = split_prediction_into_many(test_case, "\n")
    assert len(split_predictions) == 2
    assert split_predictions[0]["text"] == "a"
    assert split_predictions[0]["start"] == 5
    assert split_predictions[0]["end"] == 6
    assert split_predictions[1]["text"] == "a"
    assert split_predictions[1]["start"] == 9
    assert split_predictions[1]["end"] == 10
