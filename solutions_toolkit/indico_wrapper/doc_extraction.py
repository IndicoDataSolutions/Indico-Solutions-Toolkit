from typing import List
from indico.queries import (
    DocumentExtraction,
    JobStatus
)
from solutions_toolkit.indico_wrapper import IndicoWrapper
from solutions_toolkit.ocr import OnDoc
from solutions_toolkit.ocr import StandardOcr


class DocExtraction(IndicoWrapper):
    """
    Class to support DocumentExtraction-related API calls
    """

    def __init__(self, host_url, api_token_path=None, api_token=None, **kwargs):
        super().__init__(
            host_url, api_token_path=api_token_path, api_token=api_token, **kwargs
        )

    def get_extraction_jobs(self, preset_config: str, pdf_filepaths: List) -> List:
        """
        Args:
            preset_config (str): Preset configuration setting
            pdf_filepaths (List[str]): List of paths to local documents you would like to submit for extraction

        Returns:
            jobs (List): List of job ids
        """
        jobs = self.indico_client.call(
            DocumentExtraction(files=pdf_filepaths, json_config={"preset_config": preset_config}))
        return jobs

    def get_extracted_data(self, preset_config: str, pdf_filepaths: List):
        """
        Args:
            preset_config (str): Preset configuration setting
            pdf_filepaths (List): List of paths to local documents you would like to submit for extraction

        Returns:
            extracted_data: data from DocumentExtraction
        """
        jobs = self.get_extraction_jobs(preset_config, pdf_filepaths)
        if len(jobs) == 1:
            job = self.indico_client.call(JobStatus(id=jobs[0].id, wait=True))
            extracted_data = self.get_storage_object(job.result)
            return extracted_data
        elif len(jobs) > 1:
            extracted_data = {}
            for ind, job in enumerate(jobs):
                file = pdf_filepaths[ind]
                ocr = self.indico_client.call(JobStatus(id=job.id, wait=True))
                result = self.get_storage_object(ocr.result)
                extracted_data[file] = result
            return extracted_data

    def get_ocr_objects(self, preset_config: str, pdf_filepaths: List):
        results = self.get_extracted_data(preset_config, pdf_filepaths)
        if len(pdf_filepaths) == 1:
            if preset_config == "ondocument":
                results = OnDoc(results)
            elif preset_config == "standard":
                results = StandardOcr(results)
        elif len(pdf_filepaths) > 1:
            for result in results:
                if preset_config == "ondocument":
                    results[result] = OnDoc(results[result])
                elif preset_config == "standard":
                    results[result] = StandardOcr(results[result])
        return results

    def get_doc_full_text(self, preset_config: str, pdf_filepaths: List):
        results = self.get_ocr_objects(preset_config, pdf_filepaths)
        if len(pdf_filepaths) == 1:
            results = results.full_text
        elif len(pdf_filepaths) > 1:
            for result in results:
                results[result] = results[result].full_text
        return results

    def get_doc_page_texts(self, preset_config: str, pdf_filepaths: List):
        results = self.get_ocr_objects(preset_config, pdf_filepaths)
        if len(pdf_filepaths) == 1:
            results = results.page_texts
        elif len(pdf_filepaths) > 1:
            for result in results:
                results[result] = results[result].page_texts
        return results

    def get_doc_page_results(self, preset_config: str, pdf_filepaths: List):
        results = self.get_ocr_objects(preset_config, pdf_filepaths)
        if len(pdf_filepaths) == 1:
            results = results.page_results
        elif len(pdf_filepaths) > 1:
            for result in results:
                results[result] = results[result].page_results
        return results
