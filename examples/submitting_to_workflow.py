from indico_toolkit.indico_wrapper import Workflow
from indico_toolkit.pipelines import FileProcessing
from indico_toolkit import create_client

WORKFLOW_ID = 1418
HOST = "app.indico.io"
API_TOKEN_PATH = "./indico_api_token.txt"

# Instantiate the workflow class
client = create_client(HOST, API_TOKEN_PATH)
wflow = Workflow(client)

# Collect files to submit
fp = FileProcessing()
fp.get_file_paths_from_dir("./datasets/disclosures/")

# Submit documents, await the results and write the results to CSV in batches of 10
for paths in fp.batch_files(batch_size=10):
    submission_ids = wflow.submit_documents_to_workflow(WORKFLOW_ID, paths)
    submission_results = wflow.get_submission_results_from_ids(submission_ids)
    for filename, result in zip(paths, submission_results):
        result.predictions.to_csv("./results.csv", filename=filename, append_if_exists=True)
