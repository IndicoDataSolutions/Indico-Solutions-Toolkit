from indico import IndicoClient

from tests.conftest import API_TOKEN_PATH, HOST_URL
from solutions_toolkit.indico_wrapper import Workflow
from solutions_toolkit.ocr import OnDoc


def test_workflow_init():
    workflow = Workflow(
        HOST_URL, 
        api_token_path=API_TOKEN_PATH,
        verify_ssl=False,
        requests_params={"test":True}
    )
    assert isinstance(workflow.indico_client, IndicoClient)
    assert workflow.indico_client.config.verify_ssl == False
    assert workflow.indico_client.config.requests_params == {"test":True}


def test_submit_documents_to_workflow(workflow_wrapper, pdf_filepath, workflow_id):
    sub_ids = workflow_wrapper.submit_documents_to_workflow(workflow_id=workflow_id, pdf_filepaths=[pdf_filepath])
    assert len(sub_ids) == 1
    assert isinstance(sub_ids[0], int)


def test_get_ondoc_ocr_from_etl_url(workflow_wrapper, module_submission_results):
    etl_url = module_submission_results["etl_output"]
    on_doc = workflow_wrapper.get_ondoc_ocr_from_etl_url(etl_url)
    assert isinstance(on_doc, OnDoc)
    assert on_doc.total_pages == 8
