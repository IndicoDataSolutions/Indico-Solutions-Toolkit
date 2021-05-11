from typing import List
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
from solutions_toolkit.indico_wrapper import IndicoWrapper

# TODO: API consistency, sometimes dataset_id as kwargs other times expects w/ instantiation

class Datasets(IndicoWrapper):
    def __init__(
        self, client: IndicoClient, dataset_id: int = None
    ):
        self.client = client
        self.dataset_id = dataset_id

    def get_dataset(self):
        return self.client.call(GetDataset(self.dataset_id))

    def create_export(self, **kwargs):
        return self.client.call(
            CreateExport(dataset_id=self.dataset_id, **kwargs)
        )

    def download_export(self, export_id):
        return self.client.call(DownloadExport(export_id))

    def add_to_dataset(self, filepaths: List[str]) -> Dataset:
        dataset = self._upload_files(filepaths)
        return self._process_uploaded_files(dataset)

    def _upload_files(self, filepaths):
        return self.client.call(
            AddFiles(dataset_id=self.dataset_id, files=filepaths)
        )

    def _process_uploaded_files(self, dataset):
        datafile_ids = [f.id for f in dataset.files if f.status == "DOWNLOADED"]
        return self.client.call(
            ProcessFiles(dataset_id=dataset.id, datafile_ids=datafile_ids, wait=True)
        )

    def create_dataset(self, filepaths: List[str], name: str) -> Dataset:
        dataset = self.client.call(
            CreateDataset(
                name=name,
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

    def get_dataset_files(self) -> List[dict]:
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
