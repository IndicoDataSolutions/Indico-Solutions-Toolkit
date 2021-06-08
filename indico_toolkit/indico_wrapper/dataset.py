from typing import List
from functools import wraps
import pandas as pd
from indico import IndicoClient
from indico.types import Dataset
from indico.queries import (
    GetDataset,
    CreateDataset,
    CreateExport,
    DownloadExport,
    AddFiles,
    ProcessFiles,
    DeleteDataset,
)
from indico_toolkit.indico_wrapper import IndicoWrapper


def dataset_id_required(fn):
    """
    'Datasets' optionally requires an ID on instantiation. For methods that require that it exists, 
    throw a runtimeError if 'dataset_id' not set.
    """

    @wraps(fn)
    def check_dataset_id(self, *args, **kwargs):
        if not isinstance(self.dataset_id, int):
            raise RuntimeError(
                "You must set the 'dataset_id' attribute to use this method"
            )
        return fn(self, *args, **kwargs)

    return check_dataset_id


class Datasets(IndicoWrapper):
    def __init__(self, client: IndicoClient, dataset_id: int = None):
        self.client = client
        self.dataset_id = dataset_id

    @dataset_id_required
    def get_dataset(self):
        return self.client.call(GetDataset(self.dataset_id))

    @dataset_id_required
    def download_export(self, **kwargs) -> pd.DataFrame:
        export_id = self._create_export(**kwargs)
        return self.client.call(DownloadExport(export_id))

    def add_files_to_dataset(self, filepaths: List[str]) -> Dataset:
        dataset = self._upload_files(filepaths)
        return self._process_uploaded_files(dataset)

    def create_dataset(self, filepaths: List[str], dataset_name: str) -> Dataset:
        dataset = self.client.call(CreateDataset(name=dataset_name, files=filepaths,))
        self.dataset_id = dataset.id
        return dataset

    def delete_dataset(self, dataset_id: int) -> bool:
        """
        Returns True if operation is succesful
        """
        return self.client.call(DeleteDataset(id=dataset_id))

    @dataset_id_required
    def get_dataset_metadata(self) -> List[dict]:
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
            graphql_query=query, variables={"id": self.dataset_id}
        )
        return dataset["dataset"]["files"]
    
    @dataset_id_required
    def get_col_name_by_id(self, col_id: int) -> str:
        dataset = self.get_dataset()
        return next(c.name for c in dataset.datacolumns if c.id == col_id)

    def _create_export(self, **kwargs) -> int:
        """
        Returns export ID
        """
        export = self.client.call(CreateExport(dataset_id=self.dataset_id, **kwargs))
        return export.id

    def _process_uploaded_files(self, dataset: Dataset) -> Dataset:
        datafile_ids = [f.id for f in dataset.files if f.status == "DOWNLOADED"]
        return self.client.call(
            ProcessFiles(dataset_id=dataset.id, datafile_ids=datafile_ids, wait=True)
        )

    def _upload_files(self, filepaths):
        return self.client.call(AddFiles(dataset_id=self.dataset_id, files=filepaths))
