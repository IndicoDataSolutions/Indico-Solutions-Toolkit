
# Indico-Toolkit
A library to assist Indico IPA development

### Available Functionality
The indico-toolkit provides classes and functions to help achieve the following:
* Easy batch workflow submission and retrieval.[[Example](./examples/submitting_to_workflow.py)] / [[Module](/indico_toolkit/indico_wrapper/workflow.py)]
* Classes that simplify dataset/doc-extraction functionality. [[Example](./examples/dataset_tasks.py)] / [[Module](/indico_toolkit/indico_wrapper/dataset.py)] 
* Tools to assist with positioning, e.g. row association, distance between preds, relative position validation. [[Example](./examples/row_association.py)] / [[Module](/indico_toolkit/association/association.py)]
* Get metrics for all model IDs in a model group to see how well fields are performing after more labeling. [[Example](./examples/model_metrics.py)] / [[Module](/indico_toolkit/metrics/metrics.py)]
* Compare two models via bar plot and data tables. [[Example](./examples/model_metrics.py)] / [[Module](/indico_toolkit/metrics/plotting.py)]
* Highlighting extraction predictions on source PDFs. [[Example](./examples/pdf_highlighter.py)] / [[Module](/indico_toolkit/highlighter/highlighter.py)]
* Staggered loop learning retrieval and reformatting. [[Example](./examples/staggered_loop.py)] / [[Module](/indico_toolkit/staggered_loop/staggered_loop.py)]
* Train a document classification model without labeling. [[Example](./examples/staggered_loop.py)] / [[Module](/indico_toolkit/staggered_loop/staggered_loop.py)]
* Train a first page classification model (for bundle splitting) without labeling. [[Example](./examples/staggered_loop.py)] / [[Module](/indico_toolkit/staggered_loop/staggered_loop.py)]
* Helpful Scripted/Auto Review processing and submission. [[Example](./examples/auto_review_predictions.py)] / [[Module](/indico_toolkit/auto_review/auto_reviewer.py)]
* Common manipulation of prediction/workflow results.
* Objects to simplify parsing OCR responses.
* Snapshot merging and manipulation [[Example](./examples/merge_snapshots.py)] / [[Module](/indico_toolkit/snapshots/snapshot.py)]
* Class to spoof a human reviewer. [[Module](/indico_toolkit/indico_wrapper/reviewer.py)]

### Installation
```
pip install indico_toolkit
```
* Note: If you are on a version of the Indico IPA platform pre-5.1, then install indico-toolkit==1.2.3.
* If you want to use PdfHighlighter, install with `pip install 'indico_toolkit[full]'` as PyMuPDF is an optional dependency.

### Example Useage
For scripted examples on how to use the toolkit, see the [examples directory](https://github.com/IndicoDataSolutions/Indico-Solutions-Toolkit/tree/main/examples) 

### Tests
To run the test suite you will need to set the following environment variables: HOST_URL, API_TOKEN_PATH.
You can also set WORKFLOW_ID (workflow w/ single extraction model), MODEL_NAME (extraction model name) 
and DATASET_ID (uploaded dataset). If you don't set these 3 env variables, test configuration will 
upload a dataset and create a workflow. 
```
pytest
```
To see test coverage
```
coverage run --omit 'venv/*' -m pytest
coverage report -m
```

### Example 
How to get prediction results and write the results to CSV
```
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

```

### Contributing

If you are adding new features to Indico Toolkit, make sure to:

* Add robust integration and unit tests.
* Add a sample usage script to the 'examples/' directory.
* Add a bullet point for what the feature does to the list at the top of this README.md.
* Ensure the full test suite is passing locally before creating a pull request.
* Add doc strings for methods where usage is non-obvious.
* If you are using new pip installed libraries, make sure they are added to the setup.py and pyproject.toml.
