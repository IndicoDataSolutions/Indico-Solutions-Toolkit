from indico import IndicoClient, types
import pytest
from indico.errors import IndicoRequestError

from indico_toolkit.indico_wrapper import IndicoWrapper, retry
from indico_toolkit.types import Extractions


@pytest.fixture(scope="module")
def indico_wrapper(indico_client):
    return IndicoWrapper(indico_client)


@pytest.fixture(scope="module")
def storage_url(indico_wrapper, pdf_filepath):
    return indico_wrapper.create_storage_urls([pdf_filepath])[0]


def test_create_storage_urls(indico_wrapper, pdf_filepath):
    storage_urls = indico_wrapper.create_storage_urls([pdf_filepath])
    assert len(storage_urls) == 1
    assert isinstance(storage_urls[0], str)


def test_get_storage_object(indico_wrapper, storage_url):
    storage_object = indico_wrapper.get_storage_object(storage_url)
    assert isinstance(storage_object, bytes)


def test_get_storage_object_retry(indico_wrapper, storage_url):
    with pytest.raises(IndicoRequestError):
        _ = indico_wrapper.get_storage_object(storage_url + "bad", num_retries=1)
    

def test_retry_decor():
    @retry(Exception)
    def no_exceptions():
        return True
    
    @retry((RuntimeError, ConnectionError))
    def raises_exceptions(num_retries=10):
        raise RuntimeError("Test runtime fail")
    
    assert no_exceptions()
    with pytest.raises(RuntimeError):
        raises_exceptions()
    


def test_graphQL_request(indico_wrapper, dataset_obj):
    query = """
    query getSharknadoDataset($id: Int!) {
        dataset(id: $id) {
            id
            status
        }
    }
    """
    response = indico_wrapper.graphQL_request(query, {"id": dataset_obj.id})
    assert response["dataset"]["id"] == int(dataset_obj.id)
    assert response["dataset"]["status"] == "COMPLETE"

def test_graphQL_request_retry(indico_wrapper):
    query = """
    query getSharknadoDataset($id: Int!) {
        dataset(id: $id) {
            id
            status
        }
    }
    """
    with pytest.raises(IndicoRequestError):
        _ = indico_wrapper.graphQL_request(query, {"id": 1})


def test_get_predictions_with_model_id(indico_wrapper, extraction_model_id):
    sample_text = ["Some random sample text written by Scott Levin from Indico"]
    result = indico_wrapper.get_predictions_with_model_id(extraction_model_id, sample_text)
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], Extractions)
