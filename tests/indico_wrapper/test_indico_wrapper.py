from indico import IndicoClient, types
from indico.queries import CreateStorageURLs
from indico_toolkit.indico_wrapper import IndicoWrapper

def test_get_storage_object(indico_client, pdf_filepath):
    indico_wrapper = IndicoWrapper(indico_client)
    # TODO: make CreateStorageURLs a method of IndicoWrapper
    storage_urls = indico_wrapper.client.call(
        CreateStorageURLs(files=[pdf_filepath])
    )
    storage_object = indico_wrapper.get_storage_object(storage_urls[0])
    assert isinstance(storage_object, bytes)

def test_graphQL_request(indico_client, dataset_obj):
    query = """
    query getSharknadoDataset($id: Int!) {
        dataset(id: $id) {
            id
            status
        }
    }
    """
    indico_wrapper = IndicoWrapper(indico_client)
    response = indico_wrapper.graphQL_request(query, {"id": dataset_obj.id})
    assert response["dataset"]["id"] == int(dataset_obj.id)
    assert response["dataset"]["status"] == "COMPLETE"
