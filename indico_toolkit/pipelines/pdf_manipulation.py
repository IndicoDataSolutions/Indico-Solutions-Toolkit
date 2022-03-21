from typing import List
from functools import wraps
import fitz
from indico_toolkit import ToolkitInputError


def ensure_doc_close(fn):
    """
    If an exception is raised while PDF is open, ensure that opened PDF is closed 
    """

    @wraps(fn)
    def close_doc(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except Exception as e:
            self.close_doc()
            raise e

    return close_doc


class ManipulatePDF:
    def __init__(self, path_to_pdf: str):
        """
        Class to support common manipulations to a local PDF document

        Args:
            path_to_pdf (str): path to your PDF
        """
        self.path_to_pdf: str = path_to_pdf
        self._doc = fitz.open(path_to_pdf)

    @ensure_doc_close
    def write_subset_of_pages(self, output_path: str, page_numbers: List[int], **kwargs):
        """
        Write a subset of a PDF's pages to disc

        Args:
            output_path (str): path to write PDF to (if you want to overwrite make the same as original pdf)
            page_numbers (List[int]): a list of the page numbers included in the subset
        """
        self._validate_page_in_range(max(page_numbers))
        self._doc.select(page_numbers)
        self._doc.save(output_path, **kwargs)

    @ensure_doc_close
    def get_page_text(self, page_number: int) -> str:
        """
        Get the text from the PDF page. 
        NOTE: this is not a replacement for OCR and only meaningful with native PDFs.
        """
        self._validate_page_in_range(page_number)
        return self._doc.get_page_text(page_number)

    def close_doc(self):
        self._doc.close()

    def _validate_page_in_range(self, page_number: int):
        if self.page_count < page_number:
            raise ToolkitInputError(
                f"Document only has {self.page_count} pages, but you selected {page_number}"
            )

    @property
    def page_count(self) -> int:
        return self._doc.pageCount
