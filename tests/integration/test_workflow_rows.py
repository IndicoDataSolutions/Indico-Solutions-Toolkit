from indico_toolkit.association import LineItems
from indico_toolkit.indico_wrapper import Workflow
from tests.conftest import MODEL_NAME


def test_workflow_submit_and_get_rows(indico_client, workflow_id, pdf_filepath):
    """
    Submit a document to workflow, get results and ocr object, then association line items
    """
    wflow = Workflow(indico_client)
    sub_ids = wflow.submit_documents_to_workflow(
        workflow_id=workflow_id, pdf_filepaths=[pdf_filepath]
    )
    wflow.wait_for_submissions_to_process(sub_ids)
    sub_result = wflow.get_submission_results_from_ids([sub_ids[0]])[0]
    litems = LineItems(
        sub_result.predictions.to_list(),
        ["Previous Position", "Previous Organization"],
    )
    ondoc_ocr = wflow.get_ondoc_ocr_from_etl_url(sub_result.etl_url)
    litems.get_bounding_boxes(ocr_tokens=ondoc_ocr.token_objects)
    litems.assign_row_number()
    for pred in litems.updated_predictions.to_list():
        if pred["label"] in ["Previous Position", "Previous Organization"]:
            assert "row_number" in pred
