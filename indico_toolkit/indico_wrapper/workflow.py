import time
from typing import List
from indico import IndicoClient, IndicoRequestError
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
    UpdateWorkflowSettings,
)
from .indico_wrapper import IndicoWrapper
from indico_toolkit.ocr import OnDoc
from indico_toolkit.types import WorkflowResult


COMPLETE_FILTER = SubmissionFilter(status="COMPLETE", retrieved=False)
PENDING_REVIEW_FILTER = SubmissionFilter(status="PENDING_REVIEW", retrieved=False)


class Workflow(IndicoWrapper):
    """
    Class to support Workflow-related API calls
    """

    def __init__(self, client: IndicoClient):
        self.client = client

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
        return self.client.call(
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
        self, workflow_id: int, submission_ids: List[int] = None
    ) -> List[dict]:
        """
        Get list of completed and unretrieved workflow results
        Args:
            workflow_id (int): workflow to get completed submissions from
            submission_ids (List[int], optional): Specific IDs to retrieve, if completed. Defaults to None.

        Returns:
            List[dict]: completed submission results
        """
        submissions = self.get_complete_submission_objects(workflow_id, submission_ids)
        submission_results = self.get_submission_results_from_ids(
            [sub.id for sub in submissions]
        )
        return submission_results

    def mark_submission_as_retreived(self, submission_id: int):
        self.client.call(UpdateSubmission(submission_id, retrieved=True))

    def get_complete_submission_objects(
        self, workflow_id: int, submission_ids: List[int] = None
    ) -> List[Submission]:
        return self._get_list_of_submissions(
            workflow_id, COMPLETE_FILTER, submission_ids
        )

    def get_submission_object(self, submission_id: int) -> Submission:
        return self.client.call(GetSubmission(submission_id))

    def get_submission_results_from_ids(
        self,
        submission_ids: List[int],
        timeout: int = 75,
        ignore_exceptions: bool = False,
    ) -> List[WorkflowResult]:
        """
        Wait for submission to pass through workflow models and get result. If Review is enabled, result may be retrieved prior to human review.
        Args:
            submission_id (int): Id of submission predictions to retrieve
            timeout (int): seconds permitted for each submission prior to timing out
            ignore_exceptions (bool): if True, catch exception for unsuccessful submission

        Returns:
            List[WorkflowResult]: workflow result objects
        """
        results = []
        for subid in submission_ids:
            try:
                job = self.client.call(
                    SubmissionResult(subid, wait=True, timeout=timeout)
                )
            except IndicoRequestError as e:
                message = f"IndicoRequestError with Submission {subid}: {e}"
                self._error_handle(message, ignore_exceptions)
                continue
            if job.status != "SUCCESS":
                message = f"{job.status}! Submission {subid}: {job.result}"
                self._error_handle(message, ignore_exceptions)
                continue
            results.append(WorkflowResult(self.get_storage_object(job.result)))
        return results

    def wait_for_submissions_to_process(
        self, submission_ids: List[int], timeout: int = 120
    ) -> None:
        """
        Wait for all submissions to complete workflow processing
        """
        return self.client.call(
            WaitForSubmissions(submission_ids=submission_ids, timeout=timeout)
        )

    def submit_submission_review(self, submission_id: int, updated_predictions: dict):
        return self.client.call(
            SubmitReview(submission_id, changes=updated_predictions)
        )

    def update_workflow_settings(
        self,
        workflow_id: int,
        enable_review: bool = False,
        enable_auto_review: bool = False,
    ) -> None:
        self.client.call(
            UpdateWorkflowSettings(
                workflow_id,
                enable_review=enable_review,
                enable_auto_review=enable_auto_review,
            )
        )

    def wait_for_submission_status_complete(
        self,
        submission_id: int,
        seconds_to_sleep_each_loop: int = 2,
        max_retries: int = 5,
    ):
        retry_number = 0
        submission = self.get_submission_object(submission_id)
        while submission.status != "COMPLETE":
            time.sleep(seconds_to_sleep_each_loop)
            submission = self.get_submission_object(submission_id)
            if retry_number == max_retries:
                raise Exception(
                    f"Submission {submission_id} didn't reach status COMPLETE."
                    f"It has status: {submission.status} and errors: {submission.errors}"
                )
            retry_number += 1

    def _get_list_of_submissions(
        self,
        workflow_id: int,
        submission_filter: SubmissionFilter,
        submission_ids: List[int] = None,
    ) -> List[Submission]:
        return self.client.call(
            ListSubmissions(
                workflow_ids=[workflow_id],
                submission_ids=submission_ids,
                filters=submission_filter,
            )
        )

    def _error_handle(self, message: str, ignore_exceptions: bool):
        if ignore_exceptions:
            print(f"Ignoring exception and continuing: {message}")
        else:
            raise Exception(message)
