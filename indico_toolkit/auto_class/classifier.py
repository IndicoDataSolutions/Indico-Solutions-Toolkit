from typing import Tuple, Set
import pandas as pd
from indico import IndicoClient
from indico_toolkit.pipelines import FileProcessing
from indico_toolkit.indico_wrapper import DocExtraction

# TODO: create first page classifier methods

class AutoClassifier(DocExtraction):

    def __init__(self, client: IndicoClient, directory_path: str):
        """
        Create a CSV of OCR text alongside a class label based on a directory structure
        Args:
            client (IndicoClient): instantiated Indico Client
            directory_path (str): path to a directory containing your filepath structure
        """
        super().__init__(client)
        self.directory_path = directory_path
        self.file_paths = []
        self.file_classes = []
        self.file_texts = []
        self._fp = FileProcessing()

    def set_file_paths(self, accepted_types: Tuple[str] = ("pdf", "tiff", "tif", "doc", "docx")) -> None:
        self._fp.get_file_paths_from_dir(self.directory_path, recursive_search=True)
        self.file_paths = self._fp.file_paths

    def create_classifier(self, verbose: bool = True, batch_size: int = 5):
        """
        Collect OCR text and set file classes
        Args:
            verbose (bool, optional): Print updates on OCR progress. Defaults to True.
            batch_size (int, optional): Number of files to submit at a time. Defaults to 5.
        """
        self._set_full_doc_classes()
        for i, fpaths in enumerate(self._fp.batch_files(batch_size=batch_size)):
            if verbose:
                print(f"Starting batch {i + 1} of {len(self.file_paths) // batch_size}")
            self.file_texts.extend(
                self.run_ocr(fpaths, text_setting="full_text")
            )

    def to_csv(self, output_path: str):
        """
        Write results to a CSV that can be uploaded to the Indico IPA
        Args:
            output_path (str): path to write the CSV to
        """
        df = pd.DataFrame(
            {"text": self.file_texts, "target": self.file_classes, "filepaths": self.file_paths}
        )
        df.to_csv(output_path, index=False)

    def _set_full_doc_classes(self):
        self.file_classes = self._fp.parent_directory_of_filepaths
        self._check_class_minimum()

    def _check_class_minimum(self) -> None:
        if len(self.model_classes) < 2:
            raise Exception(
                f"You must have documents in at least 2 directories, you only have {self.model_classes}"
                )
    @property
    def model_classes(self) -> Set[str]:
        return set(self.file_classes)
