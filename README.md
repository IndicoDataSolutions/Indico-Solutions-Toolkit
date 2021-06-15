
# Indico-Toolkit
A library to assist Indico IPA development

[![Build Status][build-image]][build-url]

### Available Functionality
The indico-toolkit provides classes and functions to help achieve the following:
* Easy batch workflow submission and retrieval.
* Classes that simplify dataset/doc-extraction functionality.
* Row and line item association.
* Highlighting extraction predictions on source PDFs.
* Staggered loop learning retrieval and reformatting.
* Train a document classification model without labeling.
* Train a first page classification model (for bundle splitting) without labeling.
* Helpful Scripted/Auto Review processing and submission.
* Common manipulation of prediction/workflow results.
* Objects to simplify parsing OCR responses.
* Finder class to quicky obtain associated model/dataset/workflow Ids.
* Snapshot merging and manipulation
* Class to spoof a human reviewer.

### Installation
```
pip install indico_toolkit
```

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

<!-- Badges -->
[build-url]: https://github.com/IndicoDataSolutions/Indico-Solutions-Toolkit/actions/workflows/build.yml
[build-image]: https://github.com/IndicoDataSolutions/Indico-Solutions-Toolkit/actions/workflows/build.yml/badge.svg