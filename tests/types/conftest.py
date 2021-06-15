import pytest
import json

from indico_toolkit.types import Predictions, WorkflowResult
from indico_toolkit.types import Extractions, Classification


@pytest.fixture(scope="module")
def static_extract_results():
    with open("tests/data/samples/fin_disc_result.json", "r") as infile:
        results = json.load(infile)
    return results

@pytest.fixture(scope="module")
def static_class_results():
    with open("tests/data/samples/fin_disc_classification.json", "r") as infile:
        results = json.load(infile)
    return results

@pytest.fixture(scope="module")
def static_extract_preds(static_extract_results, model_name):
    return static_extract_results["results"]["document"]["results"][model_name]

@pytest.fixture(scope="module")
def static_class_preds(static_class_results, class_model_name):
    return static_class_results["results"]["document"]["results"][class_model_name]

@pytest.fixture(scope="function")
def extractions_obj(static_extract_preds):
    return Extractions(static_extract_preds.copy())

@pytest.fixture(scope="function")
def classification_obj(static_class_preds):
    return Classification(static_class_preds.copy())

@pytest.fixture(scope="module")
def wf_result_obj(static_extract_results):
    return WorkflowResult(static_extract_results)

