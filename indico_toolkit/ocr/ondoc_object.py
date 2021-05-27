from typing import List
import numpy as np


class OnDoc:
    """
    OnDoc is a helper class for the raw "ondocument" preset confid OCR result. Enables easy extraction
    of common datapoints into usable objects. "ondocument" is the default extraction config on the
    Indico platform.
    """

    def __init__(self, ondoc: List[dict]):
        """
        ondoc {List[dict]}: ondocument result object from indico.queries.DocumentExtraction
        """
        self.ondoc = ondoc

    @property
    def full_text(self) -> str:
        """
        Return full document text as string
        """
        return "\n".join(page["pages"][0]["text"] for page in self.ondoc)

    @property
    def page_texts(self) -> List[str]:
        """
        Return list of page-level text
        """
        return [page["pages"][0]["text"] for page in self.ondoc]

    @property
    def page_results(self) -> List[dict]:
        """
        Return list of page-level dictionary result objects
        """
        return [page["pages"][0] for page in self.ondoc]

    @property
    def block_texts(self) -> List[str]:
        """
        Return list of block-level text
        """
        return [block["text"] for page in self.ondoc for block in page["blocks"]]

    @property
    def token_objects(self) -> List[dict]:
        """
        Return list of all token objects
        """
        return [token for page in self.ondoc for token in page["tokens"]]

    @property
    def total_pages(self) -> int:
        return len(self.ondoc)

    @property
    def total_characters(self) -> int:
        return len(self.full_text)

    @property
    def total_tokens(self) -> int:
        return len(self.full_text.replace("\n", " ").split())

    @property
    def page_heights_and_widths(self) -> List[dict]:
        return [i["pages"][0]["size"] for i in self.ondoc]

    def ocr_confidence(self, metric="mean") -> float:
        """
        Return the OCR confidence (scale: 0 - 100) for all characters in the document

        metric {str}: options are "mean" or "median"
        """
        if metric not in ("mean", "median"):
            raise Exception(
                f"Metric value must be either mean or median, not '{metric}'"
            )

        if "confidence" not in self.ondoc[0]["chars"][0].keys():
            raise Exception(
                "You are likely using an old SDK version, confidence is not included"
            )

        confidence = [
            character["confidence"]
            for page in self.ondoc
            for character in page["chars"]
        ]
        if metric == "mean":
            return np.mean(confidence)
        return np.median(confidence)
