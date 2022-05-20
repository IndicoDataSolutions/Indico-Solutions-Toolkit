import os
import pandas as pd
from indico.types.export import Export
from indico import IndicoClient, IndicoRequestError
from indico_toolkit import retry, ToolkitInputError
from indico.queries import RetrieveStorageObject, DownloadExport, CreateExport
import tqdm


class Download:
    """
    Class to support downloading resources from an Indico Cluster
    """

    def __init__(self, client: IndicoClient):
        self.client = client

    def get_dataset_pdfs(
        self, dataset_id: int, labelset_id: int, output_dir: str, max_files_to_download: int = None
    ) -> int:
        """Download PDFs from an uploaded dataset to a local directory

        Args:
            dataset_id (int): Dataset ID to download from
            labelset_id (int): ID of your labelset (from teach task)
            output_dir (str): Path to directory to write PDFs
            max_files_to_download (int): = Max number of files to download (default: None = download all)

        Raises:
            ToolkitInputError: Exception if invalid directory path

        Returns:
            int: Number of files downloaded
        """
        if not os.path.isdir(output_dir):
            raise ToolkitInputError(f"Path is not a directory: {output_dir}")
        export = self._create_export(dataset_id, labelset_id)
        df = self._download_export(export.id)
        num_files_downloaded = self._download_pdfs_from_export(
            df,
            output_dir,
            f"file_name_{dataset_id}",
            f"file_url_{dataset_id}",
            max_files_to_download,
        )
        return num_files_downloaded

    def get_dataset_dataframe(
        self, dataset_id: int, labelset_id: int, file_info: bool = True, **kwargs
    ) -> pd.DataFrame:
        """Download a text representation of your dataset. For additional arguments,
        see documentation for CreateExport in the Python SDK.

        Args:
            dataset_id (int): dataset ID you're interested in
            labelset_id (int): ID of your labelset (from teach task)
            file_info (bool, optional): Include additional file level metadata. Defaults to True.

        Returns:
            pd.DataFrame: DataFrame with full document text and additional metadata
        """
        export = self._create_export(dataset_id, labelset_id, file_info=file_info, **kwargs)
        return self._download_export(export.id)

    def _download_pdfs_from_export(
        self,
        export_df: pd.DataFrame,
        output_dir: str,
        file_name_col: str,
        file_url_col: str,
        max_files_to_download: int = None,
    ) -> int:
        for i, row in tqdm.tqdm(export_df.iterrows()):
            basename = os.path.basename(row[file_name_col])
            pdf_bytes = self._retrieve_storage_object(row[file_url_col])
            with open(os.path.join(output_dir, basename), "wb") as fd:
                fd.write(pdf_bytes)
            if max_files_to_download and i + 1 == max_files_to_download:
                return max_files_to_download
        return export_df.shape[0]

    @retry((IndicoRequestError, ConnectionError))
    def _download_export(self, export_id: int) -> pd.DataFrame:
        """
        Download a dataframe representation of your dataset export
        """
        return self.client.call(DownloadExport(export_id=export_id))

    @retry((IndicoRequestError, ConnectionError))
    def _create_export(
        self, dataset_id: int, labelset_id: int, file_info: bool = True, wait: bool = True, **kwargs
    ) -> Export:
        """
        Create an export object that can be used to download datasets. For additional
        kwargs, see CreateExport docstring in the Python SDK.

        Args:
            dataset_id (int): ID of your dataset
            labelset_id (int): ID of your labelset (from teach task)
            file_info (bool, optional): whether to include additional file metadata. Defaults to True.
            wait (bool, optional): wait for export to be created. Defaults to True.

        Returns:
            Export: Description of dataset assets. See Python SDK for full object description
        """
        return self.client.call(
            CreateExport(
                dataset_id=dataset_id, file_info=file_info, labelset_id=labelset_id, wait=wait, **kwargs
            )
        )

    @retry((IndicoRequestError, ConnectionError))
    def _retrieve_storage_object(self, url: str):
        return self.client.call(RetrieveStorageObject(url))
