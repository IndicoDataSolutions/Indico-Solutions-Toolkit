from typing import List
from indico import IndicoClient
from indico.queries import (
    DocumentExtraction,
    Job,
    JobStatus
)
from solutions_toolkit.indico_wrapper import IndicoWrapper
from solutions_toolkit.ocr import OnDoc
from solutions_toolkit.ocr import StandardOcr


class DocExtraction(IndicoWrapper):
    """
    Class to support DocumentExtraction-related API calls
    """

    def __init__(self, client: IndicoClient, preset_config: None):
        self.client = client
        self.preset_config = preset_config

    def _submit_to_ocr(self, preset_config: str, pdf_filepaths: List[str]) -> List[Job]:
        """
        Args:
            preset_config (str): Preset configuration setting
            pdf_filepaths (List[str]): List of paths to local documents you would like to submit for extraction

        Returns:
            jobs (List[Job]): List of job ids
        """
        return self.client.call(
            DocumentExtraction(files=pdf_filepaths, json_config={"preset_config": preset_config}))

    def run_ocr(self, preset_config: str, pdf_filepaths: List[str]):
        """
        Args:
            preset_config (str): Preset configuration setting
            pdf_filepaths (List[str]): List of paths to local documents you would like to submit for extraction

        Returns:
            extracted_data (List[OcrObjects]): data from DocumentExtraction converted to OCR objects if applicable
        """
        jobs = self._submit_to_ocr(preset_config, pdf_filepaths)
        extracted_data = []
        for job in jobs:
            ocr = self.client.call(JobStatus(id=job.id, wait=True))
            result = self.get_storage_object(ocr.result)
            extracted_data.append(self.convert_ocr_objects(preset_config=preset_config, data=result))
        return extracted_data

    def convert_ocr_objects(self, preset_config: str, data):
        """
        Args:
            preset_config (str): Preset configuration setting
            data: data from DocumentExtraction

        Returns:
            data (OcrObject): data converted to an ocr object
        """
        if preset_config == "ondocument":
            return OnDoc(data)
        elif preset_config == "standard":
            return StandardOcr(data)
        else:
            return data
