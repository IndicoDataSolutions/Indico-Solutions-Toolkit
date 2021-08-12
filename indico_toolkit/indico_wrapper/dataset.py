from typing import List
from functools import wraps
import pandas as pd
import math
import time
from datetime import datetime
from indico import IndicoClient
from indico.types import Dataset, Workflow
from indico.queries import (
    GetDataset,
    CreateDataset,
    CreateExport,
    DownloadExport,
    AddFiles,
    ProcessFiles,
    DeleteDataset,
    CreateEmptyDataset,
    AddDataToWorkflow,
)

from indico_toolkit.indico_wrapper import IndicoWrapper
from indico_toolkit.pipelines import FileProcessing


class Datasets(IndicoWrapper):
    def __init__(self, client: IndicoClient):
        self.client = client

    def get_dataset(self, dataset_id: int):
        return self.client.call(GetDataset(dataset_id))

    def download_export(self, dataset_id: int, **kwargs) -> pd.DataFrame:
        export_id = self._create_export(dataset_id, **kwargs)
        return self.client.call(DownloadExport(export_id))

    def add_files_to_dataset(self, dataset_id: int, filepaths: List[str]) -> Dataset:
        """
        Upload documents to an existing dataset and wait for them to OCR
        """
        dataset = self.client.call(
            AddFiles(dataset_id=dataset_id, files=filepaths, wait=True)
        )
        datafile_ids = [f.id for f in dataset.files if f.status == "DOWNLOADED"]
        return self.client.call(
            ProcessFiles(dataset_id=dataset_id, datafile_ids=datafile_ids, wait=True)
        )

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
        self, dataset_name: str, dataset_type: str = "DOCUMENT"
    ) -> Dataset:
        """
        Create an empty dataset
        Args:
            name (str): Name of the dataset
            dataset_type (str, optional): TEXT, IMAGE, or DOCUMENT. Defaults to "DOCUMENT".
        """
        return self.client.call(CreateEmptyDataset(dataset_name, dataset_type))

    def create_large_doc_dataset(
        self,
        dataset_name: str,
        filepaths: List[str],
        batch_size: int = 3,
        verbose: bool = True,
    ) -> Dataset:
        """
        Create a dataset and batch document uploads to not overload queue/services

        Args:
            dataset_name (str): create a name for the dataset
            filepaths (List[str]): files you want to upload
            batch_size (int, optional): number of files to process at a time. Defaults to 3.
            verbose (bool, optional): print updates as each batch processes. Defaults to True.
        """
        fp = FileProcessing(filepaths)
        dataset_id = self.create_empty_dataset(dataset_name).id
        number_of_batches = int(math.ceil(len(filepaths) / batch_size))
        for batch_fpaths in fp.batch_files(batch_size):
            dataset = self.add_files_to_dataset(dataset_id, batch_fpaths)
            if verbose:
                number_of_batches -= 1
                print(
                    f"Finished batch at {datetime.now().time()}: {number_of_batches} remaining"
                )
        return dataset

    def create_dataset(self, filepaths: List[str], dataset_name: str) -> Dataset:
        dataset = self.client.call(
            CreateDataset(
                name=dataset_name,
                files=filepaths,
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

    def _create_export(self, dataset_id: int, **kwargs) -> int:
        """
        Returns export ID
        """
        export = self.client.call(CreateExport(dataset_id=dataset_id, **kwargs))
        return export.id
