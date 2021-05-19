from typing import Tuple, Set, List
import pandas as pd
from indico import IndicoClient
from indico_toolkit.pipelines import FileProcessing
from indico_toolkit.indico_wrapper import DocExtraction


class AutoClassifier(DocExtraction):
    def __init__(self, client: IndicoClient, directory_path: str):
        """
        Create a CSV of OCR text alongside a class label based on a directory structure. 
        You sould have a base directory containing sub directories where each directory contains
        a unique file type and only that file type. 

        Example::
            base_directory/ -> Instantiate with the page to 'base_directory' as your 'directory_path'
            base_directory/invoices/ -> folder containing only invoices
            base_directory/disclosures/ -> folder containing only disclosures
            etc. etc.

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

    def set_file_paths(
        self, accepted_types: Tuple[str] = ("pdf", "tiff", "tif", "doc", "docx")
    ) -> None:
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
            self.file_texts.extend(self.run_ocr(fpaths, text_setting="full_text"))

    def to_csv(self, output_path: str):
        """
        Write results to a CSV that can be uploaded to the Indico IPA
        Args:
            output_path (str): path to write the CSV to
        """
        df = pd.DataFrame(
            {
                "text": self.file_texts,
                "target": self.file_classes,
                "filepaths": self.file_paths,
            }
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


class FirstPageClassifier(DocExtraction):
    def __init__(self, client: IndicoClient, directory_path: str):
        """
        Automatically create a 'CSV' to train a first page classification model without labeling.

        A First Page Classifier enables you to identify the first page of documents and to split 
        apart bundled documents whenever a 'first page' occurs in the bundle. The files in
        'directory_path' should contain NO bundles- all should be single documents (i.e. no
        single PDF with multiple unique files within).

        Args:
            client (IndicoClient): instantiated Indico Client
            directory_path (str): path to a directory containing your files
        """
        super().__init__(client)
        self.client = client
        self.directory_path = directory_path
        self.file_paths = []
        self.page_classes = []
        self.page_texts = []
        self.page_files = []
        self._fp = FileProcessing()

    def set_file_paths(
        self,
        accepted_types: Tuple[str] = ("pdf", "tiff", "tif", "doc", "docx"),
        recursive_search: bool = False,
    ) -> None:
        self._fp.get_file_paths_from_dir(
            self.directory_path, recursive_search=recursive_search
        )
        self.file_paths = self._fp.file_paths

    def create_classifier(self, verbose: bool = True, batch_size: int = 5):
        """
        Collect OCR text and set page-level classes and text
        Args:
            verbose (bool, optional): Print updates on OCR progress. Defaults to True.
            batch_size (int, optional): Number of files to submit at a time. Defaults to 5.
        """
        for i, fpaths in enumerate(self._fp.batch_files(batch_size=batch_size)):
            if verbose:
                print(f"Starting batch {i + 1} of {len(self.file_paths) // batch_size}")
            page_text_lists = self.run_ocr(fpaths, "page_texts")
            for doc, fpath in zip(page_text_lists, fpaths):
                self._set_page_classes(doc, fpath)

    def _set_page_classes(self, page_text_list: List[str], filepath: str):
        filename = self._fp.get_file_name_without_suffix(filepath)
        suffix = self._fp.get_file_path_suffix(filepath)
        for ind, page in enumerate(page_text_list, start=1):
            if ind == 1:
                self.page_classes.append("First Page")
            else:
                self.page_classes.append("Not First Page")
            self.page_texts.append(page)
            self.page_files.append(f"{filename}_page_{ind}{suffix}")

    def to_csv(self, output_path: str):
        """
        Write results to a CSV that can be uploaded to the Indico IPA
        Args:
            output_path (str): path to write the CSV to
        """
        df = pd.DataFrame(
            {
                "text": self.page_texts,
                "target": self.page_classes,
                "file_and_page": self.page_files,
            }
        )
        df.to_csv(output_path, index=False)
