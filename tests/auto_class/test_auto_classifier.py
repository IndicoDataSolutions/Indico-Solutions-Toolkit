import pytest
import tempfile
import os
import pandas as pd
from indico_toolkit.auto_class import AutoClassifier

def test_set_file_paths(indico_client, testdir_file_path):
    aclass = AutoClassifier(
        indico_client,
        os.path.join(testdir_file_path, "data/auto_class")
        )
    aclass.set_file_paths()
    assert len(aclass.file_paths) == 2

def test_create_classifier(indico_client, testdir_file_path):
    aclass = AutoClassifier(
        indico_client,
        os.path.join(testdir_file_path, "data/auto_class")
        )
    aclass.set_file_paths()
    aclass.create_classifier(verbose=False)
    assert len(aclass.file_texts) == 2
    assert len(aclass.file_classes) == 2
    assert "class_a" in aclass.file_classes
    assert "class_b" in aclass.file_classes
    with tempfile.NamedTemporaryFile(suffix=".csv") as tf:
        aclass.to_csv(tf.name)
        df = pd.read_csv(tf.name)
        assert df.shape[0] == 2
        assert df.shape[1] == 3
        assert "class_a" and "class_b" in df["target"].tolist()

def test_create_classifier_too_few_classes(indico_client, testdir_file_path):
    aclass = AutoClassifier(
        indico_client,
        os.path.join(testdir_file_path, "data/auto_class/class_a")
        )
    aclass.set_file_paths()
    with pytest.raises(Exception):
        aclass.create_classifier(verbose=False)
