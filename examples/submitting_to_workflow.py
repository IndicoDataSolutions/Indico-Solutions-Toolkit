from solutions_toolkit.indico_wrapper import Workflow

WORKFLOW_ID = 1418
HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"
BATCH_TO_SUBMIT = ["path/to/doc.pdf", "path/to/doc.pdf"]

# EXAMPLE 1 -> Submit a batch of documents and retrieve results

wflow = Workflow(HOST, API_TOKEN_PATH)
submission_ids = wflow.submit_documents_to_workflow(WORKFLOW_ID, BATCH_TO_SUBMIT)
submission_results = wflow.get_submission_results_from_ids(
    submission_ids, timeout=60, ignore_exceptions=False
)
