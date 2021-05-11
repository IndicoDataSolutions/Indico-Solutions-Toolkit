import os
from typing import List
from indico.queries import (
    DocumentExtraction,
    JobStatus
)

from solutions_toolkit.indico_wrapper import IndicoWrapper
from solutions_toolkit.ocr import OnDoc
from solutions_toolkit.ocr import StandardOcr


def get_file_paths(path_to_docs, accepted_paths=("pdf", "tif", "tiff")):
    file_paths = list()
    for root, _, files in os.walk(path_to_docs):
        for name in files:
            if name.lower().endswith(accepted_paths):
                file_paths.append(os.path.join(root, name))
    return file_paths


class DocExtraction(IndicoWrapper):
    """
    Class to support DocumentExtraction-related API calls
    """

    def __init__(self, host_url, api_token_path=None, api_token=None, **kwargs):
        super().__init__(
            host_url, api_token_path=api_token_path, api_token=api_token, **kwargs
        )

    def get_extraction_jobs(self, preset_config: str, file_paths: List) -> List:
        """
        Args:
            preset_config (str): Preset configuration setting
            file_paths (List[str]): Paths to local documents you would like to submit for extraction

        Returns:
            jobs (List): List of job ids
        """
        jobs = self.indico_client.call(
            DocumentExtraction(files=file_paths, json_config={"preset_config": preset_config}))
        return jobs

    def get_extracted_data(self, preset_config: str, path_to_docs: str):
        """
        Args:
            preset_config (str): Preset configuration setting
            path_to_docs (str): Path to local documents you would like to submit for extraction

        Returns:
            extracted_data: data from DocumentExtraction
        """
        file_paths = get_file_paths(path_to_docs)
        jobs = self.get_extraction_jobs(preset_config, file_paths)
        if len(jobs) == 1:
            job = self.indico_client.call(JobStatus(id=jobs[0].id, wait=True))
            extracted_data = self.get_storage_object(job.result)
            return extracted_data
        elif len(jobs) > 1:
            extracted_data = {}
            for ind, job in enumerate(jobs):
                file = file_paths[ind]
                ocr = self.indico_client.call(JobStatus(id=job.id, wait=True))
                result = self.get_storage_object(ocr.result)
                extracted_data[file] = result
            return extracted_data

    def get_ocr_objects(self, preset_config: str, path_to_docs: str):
        file_paths = get_file_paths(path_to_docs)
        results = self.get_extracted_data(preset_config, path_to_docs)
        if len(file_paths) == 1:
            if preset_config == "ondocument":
                results = OnDoc(results)
            elif preset_config == "standard":
                results = StandardOcr(results)
        elif len(file_paths) > 1:
            for result in results:
                if preset_config == "ondocument":
                    results[result] = OnDoc(results[result])
                elif preset_config == "standard":
                    results[result] = StandardOcr(results[result])
        return results

    def get_doc_full_text(self, preset_config: str, path_to_docs: str):
        file_paths = get_file_paths(path_to_docs)
        results = self.get_ocr_objects(preset_config, path_to_docs)
        if len(file_paths) == 1:
            results = results.full_text
        elif len(file_paths) > 1:
            for result in results:
                results[result] = results[result].full_text
        return results

    def get_doc_page_texts(self, preset_config: str, path_to_docs: str):
        file_paths = get_file_paths(path_to_docs)
        results = self.get_ocr_objects(preset_config, path_to_docs)
        if len(file_paths) == 1:
            results = results.page_texts
        elif len(file_paths) > 1:
            for result in results:
                results[result] = results[result].page_texts
        return results

    def get_doc_page_results(self, preset_config: str, path_to_docs: str):
        file_paths = get_file_paths(path_to_docs)
        results = self.get_ocr_objects(preset_config, path_to_docs)
        if len(file_paths) == 1:
            results = results.page_results
        elif len(file_paths) > 1:
            for result in results:
                results[result] = results[result].page_results
        return results
