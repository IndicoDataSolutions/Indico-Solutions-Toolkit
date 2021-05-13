from typing import List, Union


class CustomOcr:
    """
    CustomOcr is a helper class for the raw preset config OCR results. Enables easy extraction
    of full text and page-level text.
    """

    def __init__(self, customocr: Union[List[dict], dict]):
        """
        customocr Union[List[dict], dict]: result object from indico.queries.DocumentExtraction
        """
        self.customocr = customocr

    @property
    def full_text(self) -> str:
        """
        Return full document text as string
        """
        if "text" in self.customocr:
            return self.customocr["text"]
        else:
            raise Exception(f"JSON configuration setting does not have full text.")

    @property
    def page_texts(self) -> List[str]:
        """
        Return list of page-level text
        """
        if "pages" in self.customocr:
            return [page["text"] for page in self.customocr["pages"]]
        else:
            raise Exception(
                f"JSON configuration setting does not have page-level text."
            )
