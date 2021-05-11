from solutions_toolkit.indico_wrapper import Workflow
from solutions_toolkit import create_client

WORKFLOW_ID = 1418
HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"
BATCH_TO_SUBMIT = ["path/to/doc.pdf", "path/to/doc.pdf"]

# EXAMPLE 1 -> Submit a batch of documents and retrieve results

client = create_client(HOST, API_TOKEN_PATH)

wflow = Workflow(client)

submission_ids = wflow.submit_documents_to_workflow(WORKFLOW_ID, BATCH_TO_SUBMIT)

submission_results = wflow.get_submission_results_from_ids(submission_ids, timeout=60)

for result in submission_results:
    print(result.predictions)
