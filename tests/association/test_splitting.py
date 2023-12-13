import pytest

from indico_toolkit.association import split_prediction


def test_split_prediction_default():
    prediction = {"text": "a\nb\n\nc", "start": 10, "end": 16}
    assert list(split_prediction(prediction)) == [
        {"text": "a", "start": 10, "end": 11},
        {"text": "b", "start": 12, "end": 13},
        {"text": "c", "start": 15, "end": 16},
    ]


def test_split_prediction_no_splits():
    prediction = {"text": "no line breaks", "start": 0, "end": 14}
    assert list(split_prediction(prediction)) == [prediction]


def test_split_prediction_regex():
    prediction = {"text": "a, a ,, b", "start": 10, "end": 19}
    assert list(split_prediction(prediction, r"[,\s]+")) == [
        {"text": "a", "start": 10, "end": 11},
        {"text": "a", "start": 13, "end": 14},
        {"text": "b", "start": 18, "end": 19},
    ]
