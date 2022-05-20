from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import time
from tqdm import tqdm
from indico import IndicoClient
from indico.client.request import Debouncer
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
    GetDatasetFileStatus,
)
from indico.queries.datasets import _UploadDatasetFiles, _AddFiles, _ProcessFiles
from indico_toolkit.indico_wrapper import IndicoWrapper
from indico_toolkit.pipelines import FileProcessing


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

    def create_dataset(self, filepaths: List[str], dataset_name: str) -> Dataset:
        dataset = self.client.call(
            CreateDataset(
                name=dataset_name,
                files=filepaths,
            )
        )
        self.dataset_id = dataset.id
        return dataset

    def create_large_doc_dataset(
        self,
        dataset_name: str,
        filepaths: List[str],
        num_threads: int = 3,
        upload_batch_size: int = 3,
        add_files_batch_size: int = 100,
        process_batch_size: int = 5,
        max_download_checks: int = 25,
    ):
        """
        Uses a threadpool to upload large documents one at a time
        and add them to a new dataset

        Args:
            dataset_name (str): create a name for the dataset
            filepaths (List[str]): files you want to upload
            num_threads (int, optional): number of threads to use for file upload. Defaults to 3.
            upload_batch_size (int, optional): number of files to upload at a time. Defaults to 3.
            add_files_batch_size (int, optional): number of files to add to dataset at a time.
                                                  Defaults to 100.
            process_batch_size (int, optional): number of files to process at a time. Defaults to 5.
            max_download_checks (int, optional): number of times to poll for uploads to complete.
                                                 Necessary because documents can get stuck in a DOWNLOADING
                                                 state. Defaults to 10 (~1 minute)
        """
        fp = FileProcessing(filepaths)
        dataset_id = self.create_empty_dataset(dataset_name).id

        # Upload using an executor - take advantage of multiple uploaders on the platform
        results = self._upload_threaded(fp, num_threads, upload_batch_size)
        print("Uploaded Doucments")

        for i in tqdm(range(0, len(results), add_files_batch_size)):
            self.client.call(
                _AddFiles(
                    dataset_id=dataset_id,
                    metadata=results[i : i + add_files_batch_size],
                )
            )
        print("Added Files to dataset, waiting for documents to download")
        indico_dataset = self.client.call(GetDatasetFileStatus(id=dataset_id))

        debouncer = Debouncer(max_timeout=max_download_checks)
        while self._datafiles_downloading(
            indico_dataset, debouncer, max_download_checks
        ):
            indico_dataset = self.client.call(GetDatasetFileStatus(id=dataset_id))
            debouncer.backoff()

        print("Downloads complete, starting pdf extraction jobs")
        file_ids = [df.id for df in indico_dataset.files if df.status == "DOWNLOADED"]
        for i in tqdm(range(0, len(file_ids), process_batch_size)):
            self.client.call(
                _ProcessFiles(
                    dataset_id=dataset_id,
                    datafile_ids=file_ids[i : i + process_batch_size],
                )
            )
        print("Files processing")
        dataset = self.client.call(GetDatasetFileStatus(id=dataset_id))
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

    def _upload_datafiles(self, filepaths: List) -> List[Dict]:
        """
        Returns a list of datafile metadata
        """
        return self.client.call(_UploadDatasetFiles(files=filepaths))

    def _upload_threaded(
        self, fp: FileProcessing, num_threads: int, batch_size: int
    ) -> List[Dict]:
        """
        Returns a list of file metadata
        """
        batches = [batch_fp for batch_fp in fp.batch_files(batch_size)]
        start = time.time()
        with ThreadPoolExecutor(max_workers=num_threads) as ex:
            futures = ex.map(self._upload_datafiles, batches)
        print(f"all submitted {time.time() - start}")
        df_metadata = []
        for metadata in futures:
            df_metadata.extend(metadata)
        return df_metadata

    def _datafiles_downloading(
        self, dataset: Dataset, debouncer: Debouncer, max_checks: int
    ) -> bool:
        """
        Return True if files are downloading OR max number of checks
        has been reached
        """
        downloaded_or_failed = not all(
            f.status in ["DOWNLOADED", "FAILED"] for f in dataset.files
        )
        too_long = debouncer.timeout < max_checks
        return downloaded_or_failed and too_long
