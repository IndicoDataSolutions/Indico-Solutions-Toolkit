from typing import List, Union


class CustomOcr:
    """
    CustomOcr is a helper class for the raw preset config OCR results. Enables easy extraction
    of full text and page-level text.
    """

    def __init__(self, customocr: Union[List[dict], dict], preset_config: str):
        """
        customocr Union[List[dict], dict]: result object from indico.queries.DocumentExtraction
        """
        self.customocr = customocr
        self.preset_config = preset_config
        self.json_config = {"preset_config": preset_config}

    @property
    def full_text(self) -> str:
        """
        Return full document text as string
        """
        return self.customocr["text"]

    @property
    def page_texts(self) -> List[str]:
        """
        Return list of page-level text
        """
        if self.preset_config == "detailed" or self.preset_config == "simple":
            return [page["text"] for page in self.customocr["pages"]]
