import pytest
from indico.errors import IndicoRequestError

from indico_toolkit.indico_wrapper import IndicoWrapper
from indico_toolkit.types import Extractions


@pytest.fixture(scope="module")
def indico_wrapper(indico_client):
    return IndicoWrapper(indico_client)


@pytest.fixture(scope="module")
def storage_url(indico_wrapper, pdf_filepath):
    return indico_wrapper.create_storage_urls([pdf_filepath])[0]


def test_get_storage_object(indico_wrapper, storage_url):
    storage_object = indico_wrapper.get_storage_object(storage_url)
    assert isinstance(storage_object, bytes)


def test_get_storage_object_retry(indico_wrapper, storage_url):
    with pytest.raises(IndicoRequestError):
        _ = indico_wrapper.get_storage_object(storage_url + "bad")


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


def test_get_predictions_with_model_id(indico_wrapper, extraction_model_id):
    sample_text = ["Some random sample text written by Scott Levin from Indico"]
    result = indico_wrapper.get_predictions_with_model_id(extraction_model_id, sample_text)
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], Extractions)


def test_create_storage_urls(indico_wrapper, pdf_filepath):
    storage_urls = indico_wrapper.create_storage_urls([pdf_filepath])
    assert len(storage_urls) == 1
    assert isinstance(storage_urls[0], str)
