import pytest
import os
from indico_toolkit import ToolkitInputError
from indico_toolkit.snapshots import Snapshot


@pytest.fixture(scope="session")
def snapshot_csv_path(testdir_file_path):
    return os.path.join(testdir_file_path, "data/snapshots/snapshot.csv")


def test_instantiation_wo_params(snapshot_csv_path):
    snap = Snapshot(snapshot_csv_path)
    assert snap.text_col == "document"
    assert snap.label_col == "question_2268"
    assert snap.file_name_col == "file_name_9123"
    assert isinstance(snap._df[snap.label_col].iloc[0], list)
    assert isinstance(snap._df[snap.label_col].iloc[0][0], dict)


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
    assert isinstance(snap._df[snap.label_col].iloc[0], list)
    assert isinstance(snap._df[snap.label_col].iloc[0][0], dict)


def test_instantiation_bad_label_col(snapshot_csv_path):
    with pytest.raises(ToolkitInputError):
        Snapshot(
            snapshot_csv_path, label_col="file_name_9123",
        )


def test_remove_extraction_labels(snapshot_csv_path):
    snap = Snapshot(snapshot_csv_path)
    assert "Trader's Name" in [i["label"] for i in snap._df[snap.label_col].iloc[0]]
    snap.remove_extraction_labels(["Trader's Name"])
    assert "Trader's Name" not in [i["label"] for i in snap._df[snap.label_col].iloc[0]]


def test_standardize_names(snapshot_csv_path):
    snap = Snapshot(snapshot_csv_path)
    snap.standardize_column_names()
    assert "source" and "target" and "file_name" in snap._df.columns


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
    expected_length = snap2._df.shape[0] * 2
    assert snap1._df.shape[0] == expected_length
