import pytest
import pandas as pd
import tempfile
import os
from indico.types import Dataset
from indico_toolkit.indico_wrapper import Download


@pytest.fixture(scope="module")
def downloader(indico_client):
    return Download(indico_client)


def test_download_export(downloader: Download, dataset_obj: Dataset):
    df = downloader.get_dataset_dataframe(dataset_obj.id, dataset_obj.labelsets[0].id)
    assert isinstance(df, pd.DataFrame)
    assert isinstance(df["text"][0], str)


def test_download_pdfs(downloader: Download, dataset_obj: Dataset):
    with tempfile.TemporaryDirectory() as tmpdir:
        num_files = downloader.get_dataset_pdfs(
            dataset_obj.id, dataset_obj.labelsets[0].id, tmpdir, max_files_to_download=1
        )
        num_files_downloaded = len(os.listdir(tmpdir))
        assert num_files == num_files_downloaded
