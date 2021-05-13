from typing import List, Union
from indico import IndicoClient
from indico.queries import DocumentExtraction, Job
from solutions_toolkit.indico_wrapper import IndicoWrapper
from solutions_toolkit.ocr import OnDoc
from solutions_toolkit.ocr import StandardOcr
from solutions_toolkit.ocr import CustomOcr


class DocExtraction(IndicoWrapper):
    """
    Class to support DocumentExtraction-related API calls
    """

    def __init__(
        self,
        client: IndicoClient,
        preset_config: str = "standard",
        custom_config: dict = None,
    ):
        """
        Args:
            preset_config (str): Options are simple, legacy, detailed, ondocument, and standard.
        """
        self._preset_config = preset_config
        self.client = client
        self.json_config = {"preset_config": preset_config}
        if custom_config:
            self.json_config = custom_config

    def run_ocr(
        self, filepaths: List[str], text_setting: str = None
    ) -> List[Union[StandardOcr, OnDoc, CustomOcr]]:
        """
        Args:
            filepaths (List[str]): List of paths to local documents you would like to submit for extraction
            text_setting (str): Options are full_text and page_texts.

        Returns:
            extracted_data (List[Union[StandardOcr, OnDoc, CustomOcr]]): data from DocumentExtraction converted to OCR objects
        """
        jobs = self._submit_to_ocr(filepaths)
        extracted_data = []
        for ind, job in enumerate(jobs):
            status = self.get_job_status(job.id, True)
            if status.status == "SUCCESS":
                result = self.get_storage_object(status.result)
                if text_setting == "full_text":
                    extracted_data.append(self._convert_ocr_objects(result).full_text)
                elif text_setting == "page_texts":
                    extracted_data.append(self._convert_ocr_objects(result).page_texts)
                else:
                    extracted_data.append(self._convert_ocr_objects(result))
            else:
                raise Exception(f"{filepaths[ind]} {status.status}: {status.result}.")
        return extracted_data

    def _submit_to_ocr(self, filepaths: List[str]) -> List[Job]:
        return self.client.call(
            DocumentExtraction(files=filepaths, json_config=self.json_config)
        )

    def _convert_ocr_objects(
        self, extracted_data: Union[List[dict], dict]
    ) -> Union[StandardOcr, OnDoc, CustomOcr]:
        if self._preset_config == "ondocument":
            return OnDoc(extracted_data)
        elif self._preset_config == "standard" or self.json_config is None:
            return StandardOcr(extracted_data)
        else:
            return CustomOcr(extracted_data)
