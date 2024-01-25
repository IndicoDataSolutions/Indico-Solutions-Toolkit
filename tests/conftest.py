import os
import pytest
from indico.queries import (
    CreateDataset,
    AddModelGroupComponent,
    NewLabelsetArguments,
    GetWorkflow,
    GetDataset,
    JobStatus,
    DocumentExtraction,
    RetrieveStorageObject,
)
from indico import IndicoClient
from indico.errors import IndicoRequestError
from indico_toolkit import create_client
from indico_toolkit.indico_wrapper import (
    Workflow,
    DocExtraction,
)
from indico_toolkit.structure.create_structure import Structure
from indico_toolkit.structure.utils import ModelTaskType


FILE_PATH = os.path.dirname(os.path.abspath(__file__))

# The following ENV Variables must be set
HOST_URL = os.environ.get("HOST_URL")
API_TOKEN_PATH = os.environ.get("API_TOKEN_PATH")
API_TOKEN = os.environ.get("API_TOKEN")

# the following five env variables are associated as part of same extraction workflow based on
# financial disclosure CSV snapshot and associated workflow
DATASET_ID = os.environ.get("DATASET_ID")
WORKFLOW_ID = os.environ.get("WORKFLOW_ID")
TEACH_TASK_ID = os.environ.get("TEACH_TASK_ID")
MODEL_GROUP_ID = os.environ.get("MODEL_GROUP_ID")
MODEL_ID = os.environ.get("MODEL_ID")
MODEL_NAME = os.environ.get("MODEL_NAME", "Solutions Toolkit Test Model")

PDF_DATASET_ID = os.environ.get("PDF_DATASET_ID")


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
    if not DATASET_ID:
        dataset = indico_client.call(
            CreateDataset(
                name="Solutions Toolkit Test Dataset",
                files=[os.path.join(FILE_PATH, "data/samples/fin_disc_snapshot.csv")],
            )
        )
    else:
        try:
            dataset = indico_client.call(GetDataset(id=DATASET_ID))
        except IndicoRequestError:
            raise ValueError(
                f"Dataset with ID {DATASET_ID} does not exist or you do not have access to it"
            )
    return dataset


@pytest.fixture(scope="session")
def workflow_id(indico_client, dataset_obj):
    global WORKFLOW_ID
    if not WORKFLOW_ID:
        structure = Structure(indico_client)
        workflow = structure.create_workflow(name="Solutions Toolkit Test Workflow", dataset_id=dataset_obj.id)
        target_names = [
            "<PAD>",
            "Asset Value",
            "Date of Appointment",
            "Department",
            "Income Amount",
            "Liability Amount",
            "Liability Type",
            "Name",
            "Position",
            "Previous Organization",
            "Previous Position"
        ]

        workflow = structure.add_teach_task(
            task_name="Teach Task Name",
            labelset_name="Extraction Labelset",
            target_names=target_names,
            dataset_id=dataset_obj.id,
            workflow_id=workflow.id,
            model_type="annotation",
            data_column="text"
        )
        WORKFLOW_ID = workflow.id
    else:
        try:
            indico_client.call(GetWorkflow(workflow_id=WORKFLOW_ID))
        except IndicoRequestError:
            raise ValueError(
                f"Workflow with ID {WORKFLOW_ID} does not exist or you do not have access to it"
            )
    return WORKFLOW_ID


@pytest.fixture(scope="session")
def teach_task_id():
    return int(TEACH_TASK_ID)


@pytest.fixture(scope="session")
def extraction_model_group_id():
    return int(MODEL_GROUP_ID)


@pytest.fixture(scope="session")
def extraction_model_id():
    return int(MODEL_ID)


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
        [module_submission_ids[0]],
    )[0]


@pytest.fixture(scope="session")
def model_name():
    return MODEL_NAME


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
    # TODO: this can be static-- probably should be "ondoc" as well
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
    return os.path.join(testdir_file_path, "data/snapshots/updated_snapshot.csv")


@pytest.fixture(scope="session")
def old_snapshot_csv_path(testdir_file_path):
    return os.path.join(testdir_file_path, "data/snapshots/snapshot.csv")


@pytest.fixture(scope="session")
def populator_snapshot_csv_path(testdir_file_path):
    return os.path.join(testdir_file_path, "data/snapshots/populator_snapshot.csv")

@pytest.fixture(scope="session")
def pdf_dataset_obj(indico_client):
    return indico_client.call(GetDataset(PDF_DATASET_ID))
