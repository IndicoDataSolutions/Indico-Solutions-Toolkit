import pytest
import tempfile
import os
import pandas as pd
from indico_toolkit.auto_class import FirstPageClassifier


def test_set_file_paths(indico_client, testdir_file_path):
    pageclass = FirstPageClassifier(
        indico_client,
        os.path.join(testdir_file_path, "data/auto_class")
        )
    pageclass.set_file_paths(recursive_search=True)
    assert len(pageclass.file_paths) == 2

def test_create_classifier(indico_client, testdir_file_path):
    pageclass = FirstPageClassifier(
        indico_client,
        os.path.join(testdir_file_path, "data/auto_class")
        )
    pageclass.set_file_paths(recursive_search=True)
    pageclass.create_classifier(verbose=False)
    assert len(pageclass.page_texts) == 3
    assert len(pageclass.page_classes) == 3
    assert len(pageclass.page_files) == 3
    assert "sample_two_pages_page_1.pdf" and "sample_two_pages_page_2.pdf" in pageclass.page_files
    with tempfile.NamedTemporaryFile(suffix=".csv") as tf:
        pageclass.to_csv(tf.name)
        df = pd.read_csv(tf.name)
        assert df.shape[0] == 3
        assert df.shape[1] == 3
        assert df["target"].tolist().count("First Page") == 2
        assert df["target"].tolist().count("Not First Page") == 1


def test_create_classifier_no_files(indico_client, testdir_file_path):
    pageclass = FirstPageClassifier(
        indico_client,
        os.path.join(testdir_file_path, "data/auto_review/")
        )
    with pytest.raises(Exception):
        pageclass.set_file_paths(accepted_types=("pdf",))
