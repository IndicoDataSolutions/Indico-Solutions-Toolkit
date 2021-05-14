import pytest
from indico_toolkit.indico_wrapper import Datasets
from indico.types import Dataset

@pytest.fixture(scope="module")
def dataset_wrapper(indico_client, dataset_obj):
    return Datasets(indico_client, dataset_obj.id)

def test_get_dataset(dataset_wrapper):
    dataset = dataset_wrapper.get_dataset()
    assert isinstance(dataset, Dataset)

def test_create_and_download_export(dataset_wrapper):
    export = dataset_wrapper.create_export()
    assert isinstance(export.id, int)
    assert export.status == "COMPLETE"
    export_df = dataset_wrapper.download_export(export.id)
    assert isinstance(export_df["text"][0], str)

def test_add_to_dataset(dataset_wrapper, pdf_filepath):
    dataset = dataset_wrapper.add_to_dataset(filepaths=[pdf_filepath])
    assert isinstance(dataset, Dataset)

def test_get_dataset_files(dataset_wrapper):
    files_list = dataset_wrapper.get_dataset_files()
    assert isinstance(files_list, list)
    assert len(files_list) > 0

def test_create_delete_dataset(dataset_wrapper, pdf_filepath):
    dataset = dataset_wrapper.create_dataset(
        filepaths=[pdf_filepath], name="Temporary Test Dataset"
    )
    assert isinstance(dataset, Dataset)
    status = dataset_wrapper.delete_dataset(dataset.id)
    assert status == True
