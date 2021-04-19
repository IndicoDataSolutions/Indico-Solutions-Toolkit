from typing import List
from indico.queries import (
    Submission,
    SubmissionFilter,
    ListSubmissions,
    UpdateSubmission,
    GetSubmission,
    WorkflowSubmission,
    SubmissionResult,
    WaitForSubmissions,
    SubmitReview,
)

from solutions_toolkit.indico_wrapper import IndicoWrapper
from solutions_toolkit.ocr import OnDoc

COMPLETE_FILTER = SubmissionFilter(status="COMPLETE", retrieved=False)
PENDING_REVIEW_FILTER = SubmissionFilter(status="PENDING_REVIEW", retrieved=False)


class Workflow(IndicoWrapper):
    """
    Class to support Workflow-related API calls
    """

    def __init__(self, host_url, api_token_path=None, api_token=None, **kwargs):
        super().__init__(
            host_url, api_token_path=api_token_path, api_token=api_token, **kwargs
        )

    def submit_documents_to_workflow(
        self, workflow_id: int, pdf_filepaths: List[str]
    ) -> List[int]:
        """
        Args:
            workflow_id (int): Workflow to submit to
            pdf_filepaths (List[str]): Path to local documents you would like to submit
        Returns:
            List[int]: List of unique and persistent identifier for each submission.
        """
        return self.indico_client.call(
            WorkflowSubmission(workflow_id=workflow_id, files=pdf_filepaths)
        )

    def get_ondoc_ocr_from_etl_url(self, etl_url: str) -> OnDoc:
        """
        Get ondocument OCR object from workflow result etl output
        Args:
            etl_url (str): url from "etl_output" key of workflow result json
        Returns:
            OnDoc: 'ondocument' OCR object
        """
        ocr_result = []
        etl_response = self.get_storage_object(etl_url)
        for page in etl_response["pages"]:
            page_ocr = self.get_storage_object(page["page_info"])
            ocr_result.append(page_ocr)
        return OnDoc(ocr_result)

    def get_completed_submission_results(
        self, workflow_id: int, submission_ids: List[int] = []
    ) -> List[dict]:
        """
        Get list of completed and unretrieved workflow results
        Args:
            workflow_id (int): workflow to get completed submissions from
            submission_ids (List[int], optional): Specific IDs to retrieve, if completed. Defaults to [].

        Returns:
            List[dict]: completed submission results
        """
        submissions = self.get_complete_submission_objects(workflow_id, submission_ids)
        submission_results = self._get_submission_results(submissions)
        return submission_results

    def mark_submission_as_retreived(self, submission_id: int):
        self.indico_client.call(UpdateSubmission(submission_id, retrieved=True))

    def get_complete_submission_objects(
        self, workflow_id: int, submission_ids: List[int] = []
    ) -> List[Submission]:
        return self._get_list_of_submissions(
            workflow_id, COMPLETE_FILTER, submission_ids
        )

    def get_submission_object(self, submission_id: int) -> Submission:
        return self.indico_client.call(GetSubmission(submission_id))

    def get_submission_result_from_id(
        self, submission_id: int, timeout: int = 75
    ) -> dict:
        """
        Wait for submission to pass through workflow models and get result. If Review is enabled,
        result may be retrieved prior to human review.
        Args:
            submission_id (int): Id of submission predictions to retrieve

        Returns:
            dict: workflow result object
        """
        job = self.indico_client.call(
            SubmissionResult(submission_id, wait=True, timeout=timeout)
        )
        return self.get_storage_object(job.result)

    def wait_for_submissions_to_process(
        self, submission_ids: List[int], timeout: int = 120
    ) -> None:
        """
        Wait for all submissions to complete workflow processing
        """
        return self.indico_client.call(
            WaitForSubmissions(submission_ids=submission_ids, timeout=timeout)
        )

    def submit_submission_review(self, submission_id: int, updated_predictions: dict):
        return self.indico_client.call(
            SubmitReview(submission_id, changes=updated_predictions)
        )

    def _get_submission_results(self, submissions: List[Submission]) -> List[dict]:
        submission_results = []
        for sub in submissions:
            submission_results.append(self.get_storage_object(sub.result_file))
        return submission_results

    def _get_list_of_submissions(
        self,
        workflow_id: int,
        submission_filter: SubmissionFilter,
        submission_ids: List[int] = None,
    ) -> List[Submission]:
        return self.indico_client.call(
            ListSubmissions(
                workflow_ids=[workflow_id],
                submission_ids=submission_ids,
                filters=submission_filter,
            )
        )
