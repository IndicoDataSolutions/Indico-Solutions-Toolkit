import os
import pytest
import json
from collections import defaultdict
from indico.queries import CreateStorageURLs

from solutions_toolkit.indico_wrapper import IndicoWrapper


FILE_PATH = os.path.dirname(os.path.abspath(__file__))

HOST_URL = os.environ.get("HOST_URL", "Missing HOST_URL environment variable")
API_TOKEN_PATH = os.environ.get(
    "API_TOKEN_PATH", "Missing API_TOKEN_PATH environment variable"
)
DATASET_ID = os.environ.get("DATASET_ID", "Missing DATASET_ID environment variable")
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
def upload_to_workflow():
    if not WORKFLOW_ID:
        # TODO: train a model, set WORKFLOW_ID
        pass
    wrapper = IndicoWrapper(host_url=HOST_URL, api_token_path=API_TOKEN_PATH)
    pdf_filepaths = ["data/pdf_samples/fin_disc.pdf"]  # TODO
    sub_ids = wrapper.upload_to_workflow(WORKFLOW_ID, pdf_filepaths)
    return WORKFLOW_ID, sub_ids


def create_pred_label_map(predictions):
    prediction_label_map = defaultdict(list)
    for pred in predictions:
        label = pred["label"]
        prediction_label_map[label].append(pred)
    return prediction_label_map


@pytest.fixture(scope="session")
def create_export():
    wrapper = IndicoWrapper(host_url=HOST_URL, api_token_path=API_TOKEN_PATH)
    export = wrapper.create_export(DATASET_ID)
    return export.id


@pytest.fixture(scope="session")
def create_storage_urls():
    wrapper = IndicoWrapper(host_url=HOST_URL, api_token_path=API_TOKEN_PATH)
    storage_urls = wrapper.indico_client.call(
        CreateStorageURLs(files=["tests/data/pdf_samples/fin_disc.pdf"])
    )
    return storage_urls
