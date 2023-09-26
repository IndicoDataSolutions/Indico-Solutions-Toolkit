import pytest
import pandas as pd
import tempfile
import os
from indico.types import Dataset
from indico_toolkit.indico_wrapper import Download, Datasets


@pytest.fixture(scope="module")
def downloader(indico_client):
    return Download(indico_client)


@pytest.fixture(scope="module")
def snap_dset_id(dataset_obj):
    return dataset_obj.id


def test_get_uploaded_csv_dataframe(downloader: Download, snap_dset_id: int):
    df = downloader.get_uploaded_csv_dataframe(snap_dset_id)
    assert isinstance(df, pd.DataFrame)
    assert "question_1620" in df.columns, "Missing column from uploaded CSV"


def test_download_export(downloader: Download, dataset_obj: Dataset):
    df = downloader.get_snapshot_dataframe(dataset_obj.id, dataset_obj.labelsets[0].id)
    assert isinstance(df, pd.DataFrame)
    assert isinstance(df["text"][0], str)


def test_download_pdfs(downloader: Download, pdf_dataset_obj: Dataset):
    with tempfile.TemporaryDirectory() as tmpdir:
        num_files = downloader.get_dataset_pdfs(
            pdf_dataset_obj.id, pdf_dataset_obj.labelsets[0].id, tmpdir, max_files_to_download=1
        )
        num_files_downloaded = len(os.listdir(tmpdir))
        assert num_files == num_files_downloaded
