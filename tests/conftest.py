import os
import pytest
import json
from indico.queries import (
    CreateDataset,
    CreateModelGroup,
    GetWorkflow,
    GetDataset,
    UpdateWorkflowSettings,
    ListWorkflows,
    JobStatus,
    DocumentExtraction,
    RetrieveStorageObject,
)
from indico import IndicoClient
from indico.errors import IndicoRequestError
from indico_toolkit import create_client
from indico_toolkit.indico_wrapper import (
    IndicoWrapper,
    Workflow,
    Datasets,
    FindRelated,
    Reviewer,
    DocExtraction,
)


FILE_PATH = os.path.dirname(os.path.abspath(__file__))

HOST_URL = os.environ.get("HOST_URL")
API_TOKEN_PATH = os.environ.get("API_TOKEN_PATH")
API_TOKEN = os.environ.get("API_TOKEN")
MODEL_NAME = os.environ.get("MODEL_NAME", "Solutions Toolkit Test Model")
CLASS_MODEL_NAME = os.environ.get("CLASS_MODEL_NAME", "Toolkit Test Classification Model")


@pytest.fixture(scope="session")
def indico_client() -> IndicoClient:
    return create_client(HOST_URL, API_TOKEN_PATH, API_TOKEN)


@pytest.fixture(scope="session")
def testdir_file_path():
    return FILE_PATH


@pytest.fixture(scope="session")
def pdf_filepath():
    return os.path.join(FILE_PATH, "data/samples/fin_disc.pdf")


@pytest.fixture(scope="session")
def dataset_obj(indico_client):
    dataset_id = os.environ.get("DATASET_ID")
    if not dataset_id:
        dataset = indico_client.call(
            CreateDataset(
                name="Solutions Toolkit Test Dataset",
                files=[os.path.join(FILE_PATH, "data/samples/fin_disc_snapshot.csv")],
            )
        )
    else:
        try:
            dataset = indico_client.call(GetDataset(id=dataset_id))
        except IndicoRequestError:
            raise ValueError(
                f"Dataset with ID {dataset_id} does not exist or you do not have access to it"
            )
    return dataset


@pytest.fixture(scope="session")
def workflow_id(indico_client, dataset_obj):
    workflow_id = os.environ.get("WORKFLOW_ID")
    if not workflow_id:
        indico_client.call(
            CreateModelGroup(
                name="Solutions Toolkit Test Model",
                dataset_id=dataset_obj.id,
                source_column_id=dataset_obj.datacolumn_by_name("text").id,
                labelset_id=dataset_obj.labelset_by_name("question_1620").id,
                wait=True,
            )
        )
        workflow_id = indico_client.call(ListWorkflows(dataset_ids=[dataset_obj.id]))[
            0
        ].id
    else:
        try:
            indico_client.call(GetWorkflow(workflow_id=workflow_id))
        except IndicoRequestError:
            raise ValueError(
                f"Workflow with ID {workflow_id} does not exist or you do not have access to it"
            )
    return workflow_id


@pytest.fixture(scope="module")
def module_submission_ids(workflow_id, indico_client, pdf_filepath):
    workflow_wrapper = Workflow(indico_client)
    sub_ids = workflow_wrapper.submit_documents_to_workflow(workflow_id, [pdf_filepath])
    workflow_wrapper.wait_for_submissions_to_process(sub_ids)
    return sub_ids


@pytest.fixture(scope="function")
def function_submission_ids(workflow_id, indico_client, pdf_filepath):
    workflow_wrapper = Workflow(indico_client)
    sub_ids = workflow_wrapper.submit_documents_to_workflow(workflow_id, [pdf_filepath])
    workflow_wrapper.wait_for_submissions_to_process(sub_ids)
    return sub_ids


@pytest.fixture(scope="module")
def wflow_submission_result(indico_client, module_submission_ids) -> dict:
    workflow_wrapper = Workflow(indico_client)
    return workflow_wrapper.get_submission_results_from_ids(
        [module_submission_ids[0]], timeout=90
    )[0]


@pytest.fixture(scope="session")
def model_name():
    return MODEL_NAME


@pytest.fixture(scope="session")
def class_model_name():
    return CLASS_MODEL_NAME

@pytest.fixture(scope="session")
def ondoc_ocr_object(indico_client, pdf_filepath):
    job = indico_client.call(
        DocumentExtraction(
            files=[pdf_filepath], json_config={"preset_config": "ondocument"}
        )
    )
    job = indico_client.call(JobStatus(id=job[0].id, wait=True))
    extracted_data = indico_client.call(RetrieveStorageObject(job.result))
    return extracted_data


@pytest.fixture(scope="session")
def standard_ocr_object(indico_client, pdf_filepath):
    job = indico_client.call(
        DocumentExtraction(
            files=[pdf_filepath], json_config={"preset_config": "standard"}
        )
    )
    job = indico_client.call(JobStatus(id=job[0].id, wait=True))
    extracted_data = indico_client.call(RetrieveStorageObject(job.result))
    return extracted_data


@pytest.fixture(scope="session")
def doc_extraction_standard(indico_client):
    return DocExtraction(indico_client)


@pytest.fixture(scope="session")
def snapshot_csv_path(testdir_file_path):
    return os.path.join(testdir_file_path, "data/snapshots/snapshot.csv")
