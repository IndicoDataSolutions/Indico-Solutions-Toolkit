import os
import pytest
import json
from collections import defaultdict
from indico.queries import CreateStorageURLs

from solutions_toolkit.indico_wrapper import IndicoWrapper, Workflow


FILE_PATH = os.path.dirname(os.path.abspath(__file__))

HOST_URL = os.environ.get("HOST_URL")
API_TOKEN_PATH = os.environ.get("API_TOKEN_PATH")
DATASET_ID = os.environ.get("DATASET_ID")
WORKFLOW_ID = os.environ.get("WORKFLOW_ID")


@pytest.fixture(scope="session")
def three_row_invoice_preds():
    with open(
        os.path.join(FILE_PATH, "data/row_association/three_row_invoice/preds.json"),
        "r",
    ) as f:
        preds = json.load(f)
    return preds


@pytest.fixture(scope="session")
def three_row_invoice_tokens():
    with open(
        os.path.join(FILE_PATH, "data/row_association/three_row_invoice/tokens.json"),
        "r",
    ) as f:
        tokens = json.load(f)
    return tokens


@pytest.fixture(scope="session")
def auto_review_preds():
    with open(os.path.join(FILE_PATH, "data/auto_review/preds.json"), "r") as f:
        preds = json.load(f)
    return preds


@pytest.fixture(scope="session")
def auto_review_field_config():
    with open(os.path.join(FILE_PATH, "data/auto_review/field_config.json"), "r") as f:
        field_config = json.load(f)
    return field_config


@pytest.fixture(scope="session")
def workflow_and_submission_ids():
    if not WORKFLOW_ID:
        # TODO: train a model, set WORKFLOW_ID
        raise NotImplementedError
    workflow_wrapper = Workflow(host_url=HOST_URL, api_token_path=API_TOKEN_PATH)
    pdf_filepaths = [os.path.join(FILE_PATH, "data/pdf_samples/fin_disc.pdf")]
    sub_ids = workflow_wrapper.submit_documents_to_workflow(WORKFLOW_ID, pdf_filepaths)
    return WORKFLOW_ID, sub_ids


@pytest.fixture(scope="session")
def workflow_submission_results() -> dict:
    if not WORKFLOW_ID:
        # TODO: train a model, set WORKFLOW_ID
        raise NotImplementedError
    workflow_wrapper = Workflow(host_url=HOST_URL, api_token_path=API_TOKEN_PATH)
    pdf_filepaths = [os.path.join(FILE_PATH, "data/pdf_samples/fin_disc.pdf")]
    sub_ids = workflow_wrapper.submit_documents_to_workflow(WORKFLOW_ID, pdf_filepaths)
    sub_result = workflow_wrapper.get_submission_result_from_id(sub_ids[0])
    return sub_result


def create_pred_label_map(predictions):
    prediction_label_map = defaultdict(list)
    for pred in predictions:
        label = pred["label"]
        prediction_label_map[label].append(pred)
    return prediction_label_map


@pytest.fixture(scope="session")
def export_id():
    wrapper = IndicoWrapper(host_url=HOST_URL, api_token_path=API_TOKEN_PATH)
    export = wrapper.create_export(DATASET_ID)
    return export.id


@pytest.fixture(scope="session")
def storage_urls():
    wrapper = IndicoWrapper(host_url=HOST_URL, api_token_path=API_TOKEN_PATH)
    storage_urls = wrapper.indico_client.call(
        CreateStorageURLs(files=["tests/data/pdf_samples/fin_disc.pdf"])
    )
    return storage_urls


@pytest.fixture(scope="session")
def indico_wrapper():
    return IndicoWrapper(host_url=HOST_URL, api_token_path=API_TOKEN_PATH)


@pytest.fixture(scope="session")
def workflow_wrapper():
    return Workflow(host_url=HOST_URL, api_token_path=API_TOKEN_PATH)


@pytest.fixture(scope="session")
def pdf_filepaths():
    return [os.path.join(FILE_PATH, "data/pdf_samples/fin_disc.pdf")]


@pytest.fixture(scope="session")
def model_name():
    return "Toolkit Test Financial Model"