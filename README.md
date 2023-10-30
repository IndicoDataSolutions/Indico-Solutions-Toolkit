# Indico-Toolkit

A library to assist Indico IPA development

### Available Functionality

The indico-toolkit provides classes and functions to help achieve the following:

* Easy batch workflow submission and retrieval.
* Classes that simplify dataset/doc-extraction functionality.
* Tools to assist with positioning, e.g. row association, distance between preds, relative position validation.
* Tools to assist with creating and copying workflow structures.
* Get metrics for all model IDs in a model group to see how well fields are performing after more labeling.
* Compare two models via bar plot and data tables.
* Highlighting extraction predictions on source PDFs.
* A simple Staggered loop implementation to identify high error documents and inject reviewed results into dev tasks.
* Train a document classification model without labeling.
* An AutoReview class to assist with automated acceptance/rejection of model predictions.
* Common manipulation of prediction/workflow results.
* Objects to simplify parsing OCR responses.
* Snapshot merging and manipulation

### Installation

```
pip install indico_toolkit
```

* Note: if you are on Indico 6.X, install an indico_toolkit 6.X version. If you're on 5.X install a 2.X version.
* Note: If you are on a version of the Indico IPA platform pre-5.1, then install indico-toolkit==1.2.3.
* If you want to use PdfHighlighter, install with `pip install 'indico_toolkit[full]'` as PyMuPDF is an optional dependency.

### Example Useage

For scripted examples on how to use the toolkit, see the [examples directory](https://github.com/IndicoDataSolutions/Indico-Solutions-Toolkit/tree/main/examples)

### Tests

To run the test suite you will need to set the following environment variables: HOST_URL, API_TOKEN_PATH.
You can also set WORKFLOW_ID (workflow w/ single extraction model), MODEL_NAME (extraction model name)
and DATASET_ID (uploaded dataset). If you don't set these 3 env variables, test configuration will
upload a dataset and create a workflow.

Note: spacy isn't a requirement to install the package, but is a requirement to run the full test suite
as it is part of "staggered loop".

```
pytest
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
