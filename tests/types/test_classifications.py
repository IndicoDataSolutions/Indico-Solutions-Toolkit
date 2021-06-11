from copy import deepcopy
import tempfile
import pandas as pd

from indico_toolkit.types import Classifications


def test_init(static_class_preds):
    classifications = Classifications(static_class_preds)
    assert classifications._preds == static_class_preds

def test_properties(classifications_obj):
    assert classifications_obj.label == "1"
    assert len(classifications_obj.labels) == 4
    assert len(classifications_obj.confidence_scores.keys()) == 4

def test_set_confidence_key_to_max_value(classifications_obj):
    max_conf = max(classifications_obj.confidence_scores.values())
    classifications_obj.set_confidence_key_to_max_value()
    assert  classifications_obj.confidence_scores == max_conf

def test_to_csv(classifications_obj):
    duplicated_obj = deepcopy(classifications_obj)
    with tempfile.NamedTemporaryFile(suffix=".csv") as tf:
        filepath = tf.name
        classifications_obj.to_csv(filepath, filepath, append_if_exists=False)
        df = pd.read_csv(filepath)
        assert "confidence" and "label" and "filename" in df.columns
        assert df.shape == (1, 3)
        duplicated_obj.to_csv(filepath, append_if_exists=True)
        df = pd.read_csv(filepath)
        assert df.shape == (2, 3)