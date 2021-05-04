from typing import List
import indico.types
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


class Dataset(IndicoWrapper):
    def __init__(
        self, host_url, api_token_path=None, api_token=None, dataset_id=None, **kwargs
    ):
        super().__init__(
            host_url, api_token_path=api_token_path, api_token=api_token, **kwargs
        )
        self.dataset_id = dataset_id

    def get_dataset(self):
        return self.indico_client.call(GetDataset(self.dataset_id))

    def create_export(self, **kwargs):
        return self.indico_client.call(
            CreateExport(dataset_id=self.dataset_id, **kwargs)
        )

    def download_export(self, export_id):
        return self.indico_client.call(DownloadExport(export_id))

    def add_to_dataset(self, filepaths: List[str]) -> indico.types.Dataset:
        dataset = self._upload_files(filepaths)
        return self._process_uploaded_files(dataset)

    def _upload_files(self, filepaths):
        return self.indico_client.call(
            AddFiles(dataset_id=self.dataset_id, files=filepaths)
        )

    def _process_uploaded_files(self, dataset):
        datafile_ids = [f.id for f in dataset.files if f.status == "DOWNLOADED"]
        return self.indico_client.call(
            ProcessFiles(dataset_id=dataset.id, datafile_ids=datafile_ids, wait=True)
        )

    def create_dataset(self, filepaths: List[str], name: str) -> indico.types.Dataset:
        dataset = self.indico_client.call(
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
        return self.indico_client.call(DeleteDataset(id=dataset_id))

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
