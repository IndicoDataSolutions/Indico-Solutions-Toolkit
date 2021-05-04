from solutions_toolkit.indico_wrapper import Dataset
import indico.types

from tests.conftest import HOST_URL, API_TOKEN_PATH, API_TOKEN


def test_get_dataset(dataset_wrapper):
    dataset = dataset_wrapper.get_dataset()
    assert isinstance(dataset, indico.types.Dataset)


def test_create_and_download_export(dataset_wrapper):
    export = dataset_wrapper.create_export()
    assert isinstance(export.id, int)
    assert export.status == "COMPLETE"
    export_df = dataset_wrapper.download_export(export.id)
    assert isinstance(export_df["text"][0], str)


def test_add_to_dataset(dataset_wrapper, pdf_filepath):
    dataset = dataset_wrapper.add_to_dataset(filepaths=[pdf_filepath])
    assert isinstance(dataset, indico.types.Dataset)


def test_get_dataset_files(dataset_wrapper):
    files_list = dataset_wrapper.get_dataset_files()
    assert isinstance(files_list, list)
    assert len(files_list) > 0


def test_create_delete_dataset(pdf_filepath):
    function_dataset_wrapper = Dataset(
        host_url=HOST_URL, api_token_path=API_TOKEN_PATH, api_token=API_TOKEN
    )
    dataset = function_dataset_wrapper.create_dataset(
        filepaths=[pdf_filepath], name="Temporary Test Dataset"
    )
    assert isinstance(dataset, indico.types.Dataset)
    status = function_dataset_wrapper.delete_dataset(dataset.id)
    assert status == True
