"""
Highlight Indico Extraction Predictions on the source PDF
"""
from indico_toolkit.indico_wrapper import Workflow
from indico_toolkit.highlighter import Highlighter
from indico_toolkit import create_client

WORKFLOW_ID = 1418
HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"
PATH_TO_DOCUMENT = "./mydocument.pdf"
# Instantiate the workflow class
client = create_client(HOST, API_TOKEN_PATH)
wflow = Workflow(client)

# Get predictions and ondocument OCR object
submission_ids = wflow.submit_documents_to_workflow(WORKFLOW_ID, [PATH_TO_DOCUMENT])
submission_result = wflow.get_submission_results_from_ids(submission_ids)[0]
ocr_object = wflow.get_ondoc_ocr_from_etl_url(submission_result.etl_url)

# Highlight Predictions onto source document and write it to disc
highlighter = Highlighter(submission_result.predictions, PATH_TO_DOCUMENT)
highlighter.collect_tokens(ocr_object.token_objects)
highlighter.highlight_pdf("./highlighted_doc.pdf", ocr_object.page_heights_and_widths, include_toc=False)
