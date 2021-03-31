from indico import IndicoClient
from indico.queries import RetrieveStorageObject
from typing import List
import os

# TODO: Convert to WorkflowResult json object?

class Tokens:
    """
    Class for indico calls
    """

    def __init__(self, client: IndicoClient):
        """
        Initialize indico client
        Args:
        client (str): instantiated IndicoClient
        """
        self.client = client

    def get_ocr_tokens(self, workflow_result: dict) -> List[dict]:
        """
        Get ocr document tokens from etl file
        Args:
        workflow_result: Indico workflow result
        """
        etl_output = workflow_result["etl_output"]
        ocr = self.client.call(RetrieveStorageObject(etl_output))
        tokens = []
        for page in ocr["pages"]:
            page_ocr = self.client.call(RetrieveStorageObject(page["page_info"]))
            tokens.extend(page_ocr["tokens"])
        return tokens