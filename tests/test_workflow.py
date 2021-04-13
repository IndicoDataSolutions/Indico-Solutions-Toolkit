from indico import IndicoClient

from tests.conftest import API_TOKEN_PATH, HOST_URL, WORKFLOW_ID
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


def test_submit_documents_to_workflow(workflow_wrapper, pdf_filepaths):
    sub_ids = workflow_wrapper.submit_documents_to_workflow(workflow_id=WORKFLOW_ID, pdf_filepaths=pdf_filepaths)
    assert len(sub_ids) == len(pdf_filepaths)
    assert isinstance(sub_ids[0], int)


def test_get_ondoc_ocr_from_etl_url(workflow_wrapper, workflow_submission_results):
    etl_url = workflow_submission_results["etl_output"]
    on_doc = workflow_wrapper.get_ondoc_ocr_from_etl_url(etl_url)
    assert isinstance(on_doc, OnDoc)
    assert on_doc.total_pages == 8
