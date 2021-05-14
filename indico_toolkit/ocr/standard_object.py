from typing import List


class StandardOcr:
    """
    StandardOcr is a helper class for the raw "standard" preset config OCR result. Enables easy extraction
    of common datapoints into usable objects.
    """

    def __init__(self, standardocr: dict):
        """
        standardocr dict: standard result object from indico.queries.DocumentExtraction
        """
        self.standardocr = standardocr

    @property
    def full_text(self) -> str:
        """
        Return full document text as string
        """
        return self.standardocr["text"]

    @property
    def page_texts(self) -> List[str]:
        """
        Return list of page-level text
        """
        return [page["text"] for page in self.standardocr["pages"]]

    @property
    def page_results(self) -> List[dict]:
        """
        Return list of page-level dictionary result objects
        """
        return [page for page in self.standardocr["pages"]]

    @property
    def block_texts(self) -> List[str]:
        """
        Return list of block-level text
        """
        return [block["text"] for page in self.standardocr["pages"] for block in page["blocks"]]

    @property
    def total_pages(self) -> int:
        return len(self.standardocr["pages"])

    @property
    def total_characters(self) -> int:
        return len(self.full_text)
