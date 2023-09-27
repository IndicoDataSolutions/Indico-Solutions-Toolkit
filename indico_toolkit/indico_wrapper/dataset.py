from typing import List
from indico import IndicoClient
from indico.types import Dataset, Workflow, OcrEngine
from indico.queries import (
    GetDataset,
    CreateDataset,
    AddFiles,
    DeleteDataset,
    CreateEmptyDataset,
    AddDataToWorkflow,
)
from indico_toolkit.indico_wrapper import IndicoWrapper


class Datasets(IndicoWrapper):
    def __init__(self, client: IndicoClient):
        self.client = client

    def get_dataset(self, dataset_id: int):
        return self.client.call(GetDataset(dataset_id))

    def add_files_to_dataset(self, dataset_id: int, filepaths: List[str]) -> Dataset:
        """
        Upload documents to an existing dataset and wait for them to OCR
        """
        dataset = self.client.call(
            AddFiles(dataset_id=dataset_id, files=filepaths, autoprocess=True, wait=True)
        )
        return dataset

    def add_new_files_to_task(self, workflow_id: id, wait: bool = True) -> Workflow:
        """
        Add newly uploaded documents to an existing teach task given the task's associated workflow ID
        Args:
            workflow_id (id): workflow ID associated with teach task
            wait (bool, optional): wait for data to be added. Defaults to True.
        """
        workflow = self.client.call(AddDataToWorkflow(workflow_id, wait))
        if wait:
            print(f"Data added to all teach tasks associated with {workflow.id}")
        return workflow

    def create_empty_dataset(
        self, dataset_name: str, dataset_type: str = "DOCUMENT", ocr_engine: OcrEngine = OcrEngine.READAPI
    ) -> Dataset:
        """
        Create an empty dataset
        Args:
            name (str): Name of the dataset
            dataset_type (str, optional): TEXT, IMAGE, or DOCUMENT. Defaults to "DOCUMENT".
        """
        return self.client.call(CreateEmptyDataset(dataset_name, dataset_type, ocr_engine))

    def create_dataset(self, filepaths: List[str], dataset_name: str, ocr_engine: OcrEngine = OcrEngine.READAPI) -> Dataset:
        dataset = self.client.call(
            CreateDataset(
                name=dataset_name,
                files=filepaths,
                ocr_engine=ocr_engine,
            )
        )
        self.dataset_id = dataset.id
        return dataset
      
    def delete_dataset(self, dataset_id: int) -> bool:
        """
        Returns True if operation is succesful
        """
        return self.client.call(DeleteDataset(id=dataset_id))

    def get_dataset_metadata(self, dataset_id: int) -> List[dict]:
        """
        Get list of dataset files with information like file name, status, and number of pages
        """
        query = """
            query GetDataset($id: Int) {
                dataset(id: $id) {
                    id
                    name
                    files {
                        id
                        name
                        numPages
                        status
                    }
                }
            }
        """
        dataset = self.graphQL_request(
            graphql_query=query, variables={"id": dataset_id}
        )
        return dataset["dataset"]["files"]

    def get_col_name_by_id(self, dataset_id: int, col_id: int) -> str:
        dataset = self.get_dataset(dataset_id)
        return next(c.name for c in dataset.datacolumns if c.id == col_id)
