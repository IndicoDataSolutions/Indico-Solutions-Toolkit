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
    DocumentExtraction,
    RetrieveStorageObject,
    JobStatus
)
from indico.errors import IndicoRequestError
from solutions_toolkit.staggered_loop import StaggeredLoop
from solutions_toolkit.indico_wrapper import (
    IndicoWrapper,
    Workflow,
    Dataset,
    FindRelated,
    Reviewer,
)


FILE_PATH = os.path.dirname(os.path.abspath(__file__))

HOST_URL = os.environ.get("HOST_URL")
API_TOKEN_PATH = os.environ.get("API_TOKEN_PATH")
API_TOKEN = os.environ.get("API_TOKEN")
MODEL_NAME = os.environ.get("MODEL_NAME", "Solutions Toolkit Test Model")

@pytest.fixture(scope="session")
def testdir_file_path():
    return FILE_PATH

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
def dataset(indico_wrapper):
    dataset_id = os.environ.get("DATASET_ID")
    if not dataset_id:
        dataset = indico_wrapper.indico_client.call(
            CreateDataset(
                name="Solutions Toolkit Test Dataset",
                files=[os.path.join(FILE_PATH, "data/samples/fin_disc_snapshot.csv")],
            )
        )
    else:
        try:
            dataset = indico_wrapper.indico_client.call(GetDataset(id=dataset_id))
        except IndicoRequestError:
            raise ValueError(
                f"Dataset with ID {dataset_id} does not exist or you do not have access to it"
            )
    return dataset


@pytest.fixture(scope="session")
def workflow_id(indico_wrapper, dataset):
    workflow_id = os.environ.get("WORKFLOW_ID")
    if not workflow_id:
        _ = indico_wrapper.indico_client.call(
            CreateModelGroup(
                name="Solutions Toolkit Test Model",
                dataset_id=dataset.id,
                source_column_id=dataset.datacolumn_by_name("text").id,
                labelset_id=dataset.labelset_by_name("question_1620").id,
                wait=True,
            )
        )
        workflow_id = indico_wrapper.indico_client.call(
            ListWorkflows(dataset_ids=[dataset.id])
        )[0].id
    else:
        try:
            indico_wrapper.indico_client.call(GetWorkflow(workflow_id=workflow_id))
        except IndicoRequestError:
            raise ValueError(
                f"Workflow with ID {workflow_id} does not exist or you do not have access to it"
            )
    return workflow_id


@pytest.fixture(scope="module")
def module_submission_ids(workflow_id, workflow_wrapper, pdf_filepath):
    sub_ids = workflow_wrapper.submit_documents_to_workflow(workflow_id, [pdf_filepath])
    workflow_wrapper.wait_for_submissions_to_process(sub_ids)
    return sub_ids


@pytest.fixture(scope="module")
def module_submission_results(workflow_wrapper, module_submission_ids) -> dict:
    return workflow_wrapper.get_submission_results_from_ids(
        [module_submission_ids[0]], timeout=90
    )[0]


@pytest.fixture(scope="function")
def function_submission_ids(workflow_id, workflow_wrapper, pdf_filepath):
    sub_ids = workflow_wrapper.submit_documents_to_workflow(workflow_id, [pdf_filepath])
    workflow_wrapper.wait_for_submissions_to_process(sub_ids)
    return sub_ids


@pytest.fixture(scope="function")
def function_submission_results(workflow_wrapper, function_submission_ids) -> dict:
    return workflow_wrapper.get_submission_results_from_ids(
        [function_submission_ids[0]], timeout=90
    )[0]


@pytest.fixture(scope="session")
def indico_wrapper():
    return IndicoWrapper(
        host_url=HOST_URL, api_token=API_TOKEN, api_token_path=API_TOKEN_PATH
    )


@pytest.fixture(scope="session")
def workflow_wrapper():
    return Workflow(
        host_url=HOST_URL, api_token=API_TOKEN, api_token_path=API_TOKEN_PATH
    )


@pytest.fixture(scope="session")
def dataset_wrapper(dataset):
    return Dataset(
        host_url=HOST_URL,
        api_token=API_TOKEN,
        api_token_path=API_TOKEN_PATH,
        dataset_id=dataset.id,
    )


@pytest.fixture(scope="session")
def find_related_wrapper():
    return FindRelated(host_url=HOST_URL, api_token=API_TOKEN, api_token_path=API_TOKEN_PATH)


@pytest.fixture(scope="session")
def reviewer_wrapper(workflow_id):
    return Reviewer(
        host_url=HOST_URL, api_token=API_TOKEN, api_token_path=API_TOKEN_PATH, workflow_id=workflow_id
    )

@pytest.fixture(scope="session")
def stagger_wrapper():
    return StaggeredLoop(host_url=HOST_URL, api_token=API_TOKEN, api_token_path=API_TOKEN_PATH,)


@pytest.fixture(scope="session")
def pdf_filepath():
    return os.path.join(FILE_PATH, "data/samples/fin_disc.pdf")


@pytest.fixture(scope="session")
def standard_ocr_object(indico_wrapper, pdf_filepath):
    job = indico_wrapper.indico_client.call(DocumentExtraction(files=[pdf_filepath], json_config={"preset_config": "standard"}))
    job = indico_wrapper.indico_client.call(JobStatus(id=job[0].id, wait=True))
    extracted_data = indico_wrapper.indico_client.call(RetrieveStorageObject(job.result))
    return extracted_data
