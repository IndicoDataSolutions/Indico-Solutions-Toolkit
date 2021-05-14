import pytest
import json
from indico_toolkit.types import Predictions, WorkflowResult


@pytest.fixture(scope="module")
def static_results():
    with open("tests/data/samples/fin_disc_result.json", "r") as infile:
        results = json.load(infile)
    return results

@pytest.fixture(scope="module")
def static_preds(static_results, model_name):
    return static_results["results"]["document"]["results"][model_name]

@pytest.fixture(scope="function")
def predictions_obj(static_preds):
    return Predictions(static_preds.copy())

@pytest.fixture(scope="module")
def wf_result_obj(static_results):
    return WorkflowResult(static_results)

