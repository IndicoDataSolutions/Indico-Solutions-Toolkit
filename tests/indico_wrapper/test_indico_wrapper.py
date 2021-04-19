from indico import IndicoClient, types
from indico.queries import CreateStorageURLs
import pandas as pd

from solutions_toolkit.indico_wrapper import IndicoWrapper
from tests.conftest import HOST_URL, API_TOKEN_PATH


def test_indico_wrapper_init():
    indico_wrapper = IndicoWrapper(
        host_url=HOST_URL,
        api_token_path=API_TOKEN_PATH,
        verify_ssl=False,
        requests_params={"test": True},
    )
    assert isinstance(indico_wrapper.indico_client, IndicoClient)
    assert indico_wrapper.indico_client.config.verify_ssl == False
    assert indico_wrapper.indico_client.config.requests_params == {"test": True}


def test_get_storage_object(indico_wrapper, pdf_filepath):
    storage_urls = indico_wrapper.indico_client.call(
        CreateStorageURLs(files=[pdf_filepath])
    )
    storage_object = indico_wrapper.get_storage_object(storage_urls[0])
    assert isinstance(storage_object, bytes)


def test_graphQL_request(indico_wrapper, dataset_id):
    query = """
    query getSharknadoDataset($id: Int!) {
        dataset(id: $id) {
            id
            status
        }
    }
    """
    response = indico_wrapper.graphQL_request(query, {"id": dataset_id})
    assert response["dataset"]["id"] == int(dataset_id)
    assert response["dataset"]["status"] == "COMPLETE"
