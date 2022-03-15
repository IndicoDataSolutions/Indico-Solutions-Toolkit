import pytest
import os
import tempfile
from copy import deepcopy
import pandas as pd
from indico_toolkit import ToolkitInputError
from indico_toolkit.snapshots import Snapshot

# TODO: tests for exception handling


def test_instantiation_wo_params(snapshot_csv_path):
    snap = Snapshot(snapshot_csv_path)
    assert snap.text_col == "document"
    assert snap.label_col == "question_2268"
    assert snap.file_name_col == "file_name_9123"
    assert isinstance(snap.df[snap.label_col].iloc[0], list)
    assert isinstance(snap.df[snap.label_col].iloc[0][0], dict)


def test_instantiation(snapshot_csv_path):
    snap = Snapshot(
        snapshot_csv_path,
        text_col="document",
        label_col="question_2268",
        file_name_col="file_name_9123",
    )
    assert snap.text_col == "document"
    assert snap.label_col == "question_2268"
    assert snap.file_name_col == "file_name_9123"
    assert isinstance(snap.df[snap.label_col].iloc[0], list)
    assert isinstance(snap.df[snap.label_col].iloc[0][0], dict)


def test_instantiation_bad_label_col(snapshot_csv_path):
    with pytest.raises(ToolkitInputError):
        Snapshot(
            snapshot_csv_path,
            label_col="file_name_9123",
        )


def test_remove_extraction_labels(snapshot_csv_path):
    snap = Snapshot(snapshot_csv_path)
    assert "Trader's Name" in [i["label"] for i in snap.df[snap.label_col].iloc[0]]
    snap.remove_extraction_labels(["Trader's Name"])
    assert "Trader's Name" not in [i["label"] for i in snap.df[snap.label_col].iloc[0]]


def test_standardize_names(snapshot_csv_path):
    snap = Snapshot(snapshot_csv_path)
    snap.standardize_column_names()
    assert "source" and "target" and "file_name" in snap.df.columns


def test__eq__not_equal(snapshot_csv_path):
    snap1 = Snapshot(snapshot_csv_path)
    snap2 = Snapshot(snapshot_csv_path)
    snap1.standardize_column_names()
    with pytest.raises(AssertionError):
        assert snap1 == snap2


def test__eq__(snapshot_csv_path):
    snap1 = Snapshot(snapshot_csv_path)
    snap2 = Snapshot(snapshot_csv_path)
    snap1.standardize_column_names()
    snap2.standardize_column_names()
    assert snap1 == snap2


def test_append(snapshot_csv_path):
    snap1 = Snapshot(snapshot_csv_path)
    snap2 = Snapshot(snapshot_csv_path)
    snap1.standardize_column_names()
    snap2.standardize_column_names()
    snap1.append(snap2)
    expected_length = snap2.df.shape[0] * 2
    assert snap1.df.shape[0] == expected_length


def test_to_csv(snapshot_csv_path):
    snap = Snapshot(snapshot_csv_path)
    snap.standardize_column_names()
    with tempfile.NamedTemporaryFile(suffix=".csv") as tf:
        snap.to_csv(tf.name)
        df = pd.read_csv(tf.name)
        assert df.shape[1] == 3
        assert isinstance(df["target"][0], str)


def test_split_and_write_to_csv(snapshot_csv_path):
    snap = Snapshot(snapshot_csv_path)
    with tempfile.TemporaryDirectory() as dirpath:
        snap.split_and_write_to_csv(dirpath, num_splits=3, output_base_name="my_split")
        original = pd.read_csv(snapshot_csv_path)
        df1 = pd.read_csv(os.path.join(dirpath, "my_split_1.csv"))
        df2 = pd.read_csv(os.path.join(dirpath, "my_split_2.csv"))
        df3 = pd.read_csv(os.path.join(dirpath, "my_split_3.csv"))
        assert df1.shape[0] == 3
        assert df2.shape[0] == 3
        assert df3.shape[0] == 4
        full = pd.concat([df1, df2, df3]).reset_index(drop=True)
        assert full.shape[0] == original.shape[0]
        assert set(full.columns) == set(original.columns)
        assert set(full["document"].tolist()) == set(original["document"].tolist())


def test_merge_by_file_name(snapshot_csv_path):
    snap1 = Snapshot(snapshot_csv_path)
    snap2 = Snapshot(snapshot_csv_path)
    snap1.standardize_column_names()
    snap2.standardize_column_names()
    snap1.merge_by_file_name(snap2)
    expected_pred_length = len(snap2.df[snap2.label_col][0]) * 2
    assert len(snap1.df[snap1.label_col][0]) == expected_pred_length
    assert snap1.df.shape[0] == snap2.df.shape[0]
    for val in snap1.df[snap1.label_col]:
        assert isinstance(val, list)


def test_merge_by_file_name_columns_no_match(snapshot_csv_path):
    snap1 = Snapshot(snapshot_csv_path)
    snap2 = Snapshot(snapshot_csv_path)
    snap1.standardize_column_names()
    with pytest.raises(ToolkitInputError):
        snap1.merge_by_file_name(snap2)


def test_merge_by_file_name_no_filename_matches(snapshot_csv_path):
    snap1 = Snapshot(snapshot_csv_path)
    snap2 = Snapshot(snapshot_csv_path)
    snap1.standardize_column_names()
    snap2.standardize_column_names()
    snap2.df[snap2.file_name_col] = "no_match"
    original_labels = deepcopy(snap1.df[snap1.label_col].tolist())
    snap1.merge_by_file_name(snap2)
    assert snap1.df[snap1.label_col].tolist() == original_labels


def test_get_extraction_label_names(snapshot_csv_path, snapshot_classes):
    snap = Snapshot(snapshot_csv_path)
    label_list = snap.get_extraction_label_names()
    assert len(snapshot_classes) == len(label_list)
    for snapshot_class, test_class in zip(snapshot_classes, label_list):
        assert snapshot_class == test_class


def test_number_of_samples(snapshot_csv_path):
    snap = Snapshot(snapshot_csv_path)
    assert snap.number_of_samples == 10


def test_get_all_labeled_text(snapshot_csv_path):
    snap = Snapshot(snapshot_csv_path)
    labeled_text = snap.get_all_labeled_text("Trader's District")
    assert len(labeled_text) == 10
    assert isinstance(labeled_text[0], str)
    assert labeled_text[0] == "CA47"


def test_get_all_labeled_text_per_doc(snapshot_csv_path):
    snap = Snapshot(snapshot_csv_path)
    labeled_text = snap.get_all_labeled_text(
        "Trader's District", return_per_document=True
    )
    assert len(labeled_text) == 10
    assert isinstance(labeled_text[0], list)
    assert len(labeled_text[0]) == 1
    assert labeled_text[0][0] == "CA47"
