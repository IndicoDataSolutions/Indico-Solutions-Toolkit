from indico import IndicoClient
from indico.types import Submission, Job
from tests.conftest import MODEL_NAME
from solutions_toolkit.indico_wrapper import Workflow
from solutions_toolkit.ocr import OnDoc


def test_submit_documents_to_workflow(indico_client, pdf_filepath, workflow_id):
    wflow = Workflow(indico_client)
    sub_ids = wflow.submit_documents_to_workflow(
        workflow_id=workflow_id, pdf_filepaths=[pdf_filepath]
    )
    assert len(sub_ids) == 1
    assert isinstance(sub_ids[0], int)


def test_get_ondoc_ocr_from_etl_url(indico_client, wflow_submission_results):
    wflow = Workflow(indico_client)
    etl_url = wflow_submission_results["etl_output"]
    on_doc = wflow.get_ondoc_ocr_from_etl_url(etl_url)
    assert isinstance(on_doc, OnDoc)
    assert on_doc.total_pages == 2


def test_get_completed_submission_results(
    indico_client, module_submission_ids, workflow_id
):
    wflow = Workflow(indico_client)
    results = wflow.get_completed_submission_results(
        workflow_id, submission_ids=module_submission_ids
    )
    assert isinstance(results, list)


def test_mark_submission_as_retreived(indico_client, function_submission_ids):
    wflow = Workflow(indico_client)
    wflow.mark_submission_as_retreived(submission_id=function_submission_ids[0])


def test_get_complete_submission_objects(
    indico_client, workflow_id, module_submission_ids
):
    wflow = Workflow(indico_client)
    sub_list = wflow.get_complete_submission_objects(workflow_id, module_submission_ids)
    assert isinstance(sub_list, list)


def test_get_submission_object(indico_client, module_submission_ids):
    wflow = Workflow(indico_client)
    sub = wflow.get_submission_object(module_submission_ids[0])
    assert isinstance(sub, Submission)


def test_get_submission_result_from_id(indico_client, module_submission_ids):
    wflow = Workflow(indico_client)
    results = wflow.get_submission_result_from_id(module_submission_ids[0])
    predictions = results["results"]["document"]["results"][MODEL_NAME]["pre_review"]
    assert isinstance(predictions, list)
