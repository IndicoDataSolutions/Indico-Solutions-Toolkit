from indico import IndicoClient
from indico.types import Submission, Job

from tests.conftest import API_TOKEN_PATH, HOST_URL, MODEL_NAME, API_TOKEN
from solutions_toolkit.indico_wrapper import Workflow
from solutions_toolkit.ocr import OnDoc


def test_workflow_init():
    workflow = Workflow(
        HOST_URL,
        api_token_path=API_TOKEN_PATH,
        api_token=API_TOKEN,
        verify_ssl=False,
        requests_params={"test": True},
    )
    assert isinstance(workflow.indico_client, IndicoClient)
    assert workflow.indico_client.config.verify_ssl == False
    assert workflow.indico_client.config.requests_params == {"test": True}


def test_submit_documents_to_workflow(workflow_wrapper, pdf_filepath, workflow_id):
    sub_ids = workflow_wrapper.submit_documents_to_workflow(
        workflow_id=workflow_id, pdf_filepaths=[pdf_filepath]
    )
    assert len(sub_ids) == 1
    assert isinstance(sub_ids[0], int)


def test_get_ondoc_ocr_from_etl_url(workflow_wrapper, module_submission_results):
    etl_url = module_submission_results["etl_output"]
    on_doc = workflow_wrapper.get_ondoc_ocr_from_etl_url(etl_url)
    assert isinstance(on_doc, OnDoc)
    assert on_doc.total_pages == 8


def test_get_completed_submission_results(
    workflow_wrapper, module_submission_ids, workflow_id
):
    results = workflow_wrapper.get_completed_submission_results(
        workflow_id, submission_ids=module_submission_ids
    )
    assert isinstance(results, list)


def test_mark_submission_as_retreived(
    workflow_wrapper, function_submission_ids, workflow_id
):
    workflow_wrapper.mark_submission_as_retreived(
        submission_id=function_submission_ids[0]
    )


def test_get_complete_submission_objects(
    workflow_wrapper, workflow_id, module_submission_ids
):
    sub_list = workflow_wrapper.get_complete_submission_objects(
        workflow_id, module_submission_ids
    )
    assert isinstance(sub_list, list)


def test_get_submission_object(workflow_wrapper, module_submission_ids):
    sub = workflow_wrapper.get_submission_object(module_submission_ids[0])
    assert isinstance(sub, Submission)


def test_get_submission_result_from_id(
    workflow_wrapper, module_submission_ids
):
    results = workflow_wrapper.get_submission_result_from_id(module_submission_ids[0])
    predictions = results["results"]["document"]["results"][MODEL_NAME]["pre_review"]
    assert isinstance(predictions, list)


def test_submit_submission_review(
    workflow_wrapper, function_submission_ids, function_submission_results
):
    predictions = function_submission_results["results"]["document"]["results"][
        MODEL_NAME
    ]["pre_review"]
    job = workflow_wrapper.submit_submission_review(
        function_submission_ids[0], {MODEL_NAME: predictions}
    )
    assert isinstance(job, Job)
