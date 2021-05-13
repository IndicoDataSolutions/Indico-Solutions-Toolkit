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
        if self.customocr is dict and "text" in self.customocr:
            return self.customocr["text"]
        elif self.customocr is List[dict] and "pages" in self.customocr[0]:
            if "text" in self.customocr[0]["pages"][0]:
                return "\n".join(page["pages"][0]["text"] for page in self.customocr)
        raise Exception(f"JSON configuration setting does not have full text.")

    @property
    def page_texts(self) -> List[str]:
        """
        Return list of page-level text
        """
        if self.customocr is dict and "pages" in self.customocr:
            if "text" in self.customocr["pages"]:
                return [page["text"] for page in self.customocr["pages"]]
        elif self.customocr is List[dict] and "pages" in self.customocr[0]:
            if "text" in self.customocr[0]["pages"][0]:
                return [page["pages"][0]["text"] for page in self.customocr]
        raise Exception(f"JSON configuration setting does not have page-level text.")
