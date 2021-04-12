from indico import IndicoClient, types
import pandas as pd

from solutions_toolkit.indico_wrapper import IndicoWrapper
from tests.conftest import WORKFLOW_ID, HOST_URL, API_TOKEN_PATH, DATASET_ID


def test_indico_wrapper_init():
    indico_wrapper = IndicoWrapper(
        host_url=HOST_URL,
        api_token_path=API_TOKEN_PATH,
        verify_ssl=False,
        requests_params={"test":True}
    )
    assert isinstance(indico_wrapper.indico_client, IndicoClient)
    assert indico_wrapper.indico_client.config.verify_ssl == False
    assert indico_wrapper.indico_client.config.requests_params == {"test":True}


def test_get_storage_object(create_storage_urls):
    indico_wrapper = IndicoWrapper(host_url=HOST_URL, api_token_path=API_TOKEN_PATH)
    storage_urls = create_storage_urls
    storage_object = indico_wrapper.get_storage_object(storage_urls[0])
    assert isinstance(storage_object, bytes)


def test_graphQL_request():
    query = """
    query getSharknadoDataset($id: Int!) {
        dataset(id: $id) {
            id
            status
        }
    }
    """
    indico_wrapper = IndicoWrapper(host_url=HOST_URL, api_token_path=API_TOKEN_PATH)
    response = indico_wrapper.graphQL_request(query, {"id":DATASET_ID})
    assert response["dataset"]["id"] == int(DATASET_ID)
    assert response["dataset"]["status"] == "COMPLETE"


def test_get_dataset():
    indico_wrapper = IndicoWrapper(host_url=HOST_URL, api_token_path=API_TOKEN_PATH)
    dataset = indico_wrapper.get_dataset(DATASET_ID)
    assert isinstance(dataset, types.dataset.Dataset)


def test_create_export():
    indico_wrapper = IndicoWrapper(host_url=HOST_URL, api_token_path=API_TOKEN_PATH)
    export = indico_wrapper.create_export(DATASET_ID)
    assert isinstance(export.id, int)
    assert export.status == "COMPLETE"


def test_download_export(create_export):
    export_id = create_export
    indico_wrapper = IndicoWrapper(host_url=HOST_URL, api_token_path=API_TOKEN_PATH)
    export_df = indico_wrapper.download_export(export_id)
    assert isinstance(export_df["text"][0], str)
