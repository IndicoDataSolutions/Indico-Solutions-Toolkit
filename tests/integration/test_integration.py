from solutions_toolkit.row_association import Association


def test_workflow_submit_and_get_rows(workflow_wrapper, workflow_id, pdf_filepath):
    """
    Submit a document to workflow, get results and ocr object, then association line items
    """
    sub_ids = workflow_wrapper.submit_documents_to_workflow(
        workflow_id=workflow_id, pdf_filepaths=[pdf_filepath]
    )
    workflow_wrapper.wait_for_submissions_to_process(sub_ids)
    sub_result = workflow_wrapper.get_submission_result_from_id(submission_id=sub_ids[0])
    litems = Association(["Previous Position", "Previous Organization"], predictions=sub_result.predictions)
    ondoc_ocr = workflow_wrapper.get_ondoc_ocr_from_etl_url(sub_result.etl_url)
    litems.get_bounding_boxes(ocr_tokens=ondoc_ocr.token_objects)
    litems.assign_row_number()
    for pred in litems.updated_predictions:
        if pred["label"] in ["Previous Position", "Previous Organization"]:
            assert "row_number" in pred