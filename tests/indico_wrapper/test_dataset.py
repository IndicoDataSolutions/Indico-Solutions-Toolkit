import pytest
import pandas as pd
from indico_toolkit.indico_wrapper import Datasets
from indico.types import Dataset


@pytest.fixture(scope="module")
def dataset_wrapper(indico_client, dataset_obj):
    return Datasets(indico_client)


@pytest.fixture(scope="module")
def dataset_id(dataset_obj):
    return dataset_obj.id


def test_get_dataset(dataset_wrapper, dataset_id):
    dataset = dataset_wrapper.get_dataset(dataset_id)
    assert isinstance(dataset, Dataset)


def test_download_export(dataset_wrapper, dataset_id):
    df = dataset_wrapper.download_export(dataset_id)
    assert isinstance(df, pd.DataFrame)
    assert isinstance(df["text"][0], str)


def test_add_to_dataset(dataset_wrapper, dataset_id, pdf_filepath):
    dataset = dataset_wrapper.add_files_to_dataset(dataset_id, filepaths=[pdf_filepath])
    assert isinstance(dataset, Dataset)
    for f in dataset.files:
        assert f.status in ["PROCESSED", "FAILED"]


def test_get_dataset_files(dataset_wrapper, dataset_id):
    files_list = dataset_wrapper.get_dataset_metadata(dataset_id)
    assert isinstance(files_list, list)
    assert len(files_list) > 0


def test_create_delete_dataset(dataset_wrapper, pdf_filepath):
    dataset = dataset_wrapper.create_dataset(
        filepaths=[pdf_filepath], dataset_name="Temporary Test Dataset"
    )
    assert isinstance(dataset, Dataset)
    status = dataset_wrapper.delete_dataset(dataset.id)
    assert status == True


def test_create_large_doc_dataset(dataset_wrapper, pdf_filepath):
    dataset = dataset_wrapper.create_large_doc_dataset(
        "mydataset",
        [pdf_filepath, pdf_filepath],
        batch_size=1,
        verbose=False,
    )
    assert len(dataset.files) == 2
    for f in dataset.files:
        assert f.status == "PROCESSED"

