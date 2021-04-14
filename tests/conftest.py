import os
import pytest
import json
from indico.queries import CreateDataset, CreateModelGroup, GetWorkflow, GetDataset
from indico.errors import IndicoRequestError

from solutions_toolkit.indico_wrapper import IndicoWrapper, Workflow


FILE_PATH = os.path.dirname(os.path.abspath(__file__))

HOST_URL = os.environ.get("HOST_URL")
API_TOKEN_PATH = os.environ.get("API_TOKEN_PATH")
MODEL_NAME = os.environ.get("MODEL_NAME")


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
def dataset_id(indico_wrapper):
    DATASET_ID = os.environ.get("DATASET_ID")
    if not DATASET_ID:
        dataset = indico_wrapper.indico_client.call(
            CreateDataset(
                name="Solutions Toolkit Test Dataset",
                files=[os.path.join(FILE_PATH, "data/samples/fin_disc_snapshot.csv")],
            )
        )
        DATASET_ID = dataset.id
    else:
        try:
            dataset = indico_wrapper.indico_client.call(GetDataset(id=DATASET_ID))
        except IndicoRequestError:
            raise ValueError(
                f"Dataset with ID {DATASET_ID} does not exist or you do not have access to it"
            )
    return DATASET_ID


@pytest.fixture(scope="session")
def workflow_id(indico_wrapper, dataset_id):
    WORKFLOW_ID = os.environ.get("WORKFLOW_ID")
    if not WORKFLOW_ID:
        model_group = indico_wrapper.indico_client.call(
            CreateModelGroup(
                name="Solutions Toolkit Test Model",
                dataset_id=dataset_id,
                source_column_id=dataset.datacolumn_by_name("text").id,
                labelset_id=dataset.labelset_by_name("question_1620").id,
                wait=True,
            )
        )
        WORKFLOW_ID = model_group.selected_model.id
    else:
        try:
            indico_wrapper.indico_client.call(GetWorkflow(workflow_id=WORKFLOW_ID))
        except IndicoRequestError:
            raise ValueError(
                f"Workflow with ID {WORKFLOW_ID} does not exist or you do not have access to it"
            )
    return WORKFLOW_ID


@pytest.fixture(scope="session")
def session_submission_ids(workflow_id, workflow_wrapper, pdf_filepaths):
    sub_ids = workflow_wrapper.submit_documents_to_workflow(workflow_id, pdf_filepaths)
    return sub_ids


@pytest.fixture(scope="session")
def session_submission_results(workflow_wrapper, session_submission_ids) -> dict:
    sub_result = workflow_wrapper.get_submission_result_from_id(
        session_submission_ids[0], timeout=90
    )
    return sub_result


@pytest.fixture(scope="function")
def function_submission_ids(workflow_id, workflow_wrapper, pdf_filepaths):
    sub_ids = workflow_wrapper.submit_documents_to_workflow(workflow_id, pdf_filepaths)
    return sub_ids


@pytest.fixture(scope="function")
def function_submission_results(workflow_wrapper, function_submission_ids) -> dict:
    sub_result = workflow_wrapper.get_submission_result_from_id(
        session_submission_ids[0], timeout=90
    )
    return sub_result


@pytest.fixture(scope="session")
def indico_wrapper():
    return IndicoWrapper(host_url=HOST_URL, api_token_path=API_TOKEN_PATH)


@pytest.fixture(scope="session")
def workflow_wrapper():
    return Workflow(host_url=HOST_URL, api_token_path=API_TOKEN_PATH)


@pytest.fixture(scope="session")
def pdf_filepaths():
    return [os.path.join(FILE_PATH, "data/samples/fin_disc.pdf")]
