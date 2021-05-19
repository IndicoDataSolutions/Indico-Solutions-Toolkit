import pytest
import pandas as pd
from indico_toolkit.indico_wrapper import Datasets
from indico.types import Dataset

@pytest.fixture(scope="module")
def dataset_wrapper(indico_client, dataset_obj):
    return Datasets(indico_client, dataset_obj.id)


def test_dataset_id_required_decorator(indico_client):
    dset = Datasets(indico_client)
    with pytest.raises(RuntimeError):
        dset.get_dataset_metadata()

def test_get_dataset(dataset_wrapper):
    dataset = dataset_wrapper.get_dataset()
    assert isinstance(dataset, Dataset)

def test_download_export(dataset_wrapper):
    df = dataset_wrapper.download_export()
    assert isinstance(df, pd.DataFrame)
    assert isinstance(df["text"][0], str)

def test_add_to_dataset(dataset_wrapper, pdf_filepath):
    dataset = dataset_wrapper.add_files_to_dataset(filepaths=[pdf_filepath])
    assert isinstance(dataset, Dataset)

def test_get_dataset_files(dataset_wrapper):
    files_list = dataset_wrapper.get_dataset_metadata()
    assert isinstance(files_list, list)
    assert len(files_list) > 0

def test_create_delete_dataset(dataset_wrapper, pdf_filepath):
    dataset = dataset_wrapper.create_dataset(
        filepaths=[pdf_filepath], dataset_name="Temporary Test Dataset"
    )
    assert isinstance(dataset, Dataset)
    status = dataset_wrapper.delete_dataset(dataset.id)
    assert status == True
