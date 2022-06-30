from typing import List, Union
from indico import IndicoClient, IndicoRequestError
from indico.queries import (
    AddModelGroupComponent,
    GetWorkflow,
    GetDataset,
    Submission,
    SubmissionFilter,
    ListSubmissions,
    UpdateSubmission,
    GetSubmission,
    WorkflowSubmission,
    SubmitReview,
    WaitForSubmissions,
    UpdateWorkflowSettings,
    JobStatus,
)
from indico.queries.submission import SubmissionResult
from .indico_wrapper import IndicoWrapper
from indico_toolkit import ToolkitStatusError
from indico_toolkit.ocr import OnDoc
from indico.types import NewLabelsetArguments, NewQuestionnaireArguments
from indico.types import Workflow as IndicoWorkflowObject
from indico_toolkit.types import WorkflowResult


COMPLETE_FILTER = SubmissionFilter(status="COMPLETE", retrieved=False)
PENDING_REVIEW_FILTER = SubmissionFilter(status="PENDING_REVIEW", retrieved=False)


class Workflow(IndicoWrapper):
    """
    Class to support Workflow-related API calls
    """

    def __init__(self, client: IndicoClient):
        self.client = client

    def add_mg_component(
        self,
        workflow_id: int,
        dataset_id: int,
        model_name: str,
        source_col: str,
        target_col: str,
        after_component_type: str = "INPUT_OCR_EXTRACTION",
        new_labelset_args: NewLabelsetArguments = None,
        new_questionnaire_args: NewQuestionnaireArguments = None,
        model_training_options: dict = None,
        model_type: str = None,
    ) -> IndicoWorkflowObject:
        """
        Adds a new model group to a workflow, optionally with a customized questionnaire.
        Available on 5.0+ only.

        Args:
            dataset_id (int): id of the dataset that the model will be trained on
            workflow_id (int): id of the workflow that the model will belong to
            model_name (str): the name for your model
            source_col (str): the csv column that contained the text
            target_col (str): the csv column that contained the labels
            after_component_type (str): The type of the previous component, or step, that should precede this step.
                Typically, this prior component would be something like "INPUT_OCR_EXTRACTION" or "INPUT_IMAGE".
            new_labelset_args (NewLabelsetArguments): if needed, new labelset to add.
                Only use if not using labelset_column_id.
            new_questionnaire_args (NewQuestionnaireArguments): Customize the questionnaire associated with this model group.
            model_training_options (dict): Additional options for training. If the model_type is FINETUNE, this can include the base_model, which should be one of "default", "roberta", "small", "multilingual", "fast", "textcnn", or "fasttextcnn".
            model_type (str): The model type to use, defaults to the default model type for the dataset type. Valid options are "ENSEMBLE", "TFIDF_LR", "TFIDF_GBT", "STANDARD", "FINETUNE", "OBJECT_DETECTION", "RATIONALIZED", "FORM_EXTRACTION", and "DOCUMENT".
        Returns:
            Indico Workflow object with updated component list, which will contain the added Model Group
        """
        wflow = self.client.call(GetWorkflow(workflow_id))
        dataset = self.client.call(GetDataset(dataset_id))
        after_component = wflow.component_by_type(after_component_type)

        return self.client.call(
            AddModelGroupComponent(
                workflow_id=wflow.id,
                dataset_id=dataset.id,
                name=model_name,
                after_component_id=after_component.id,
                source_column_id=dataset.datacolumn_by_name(source_col).id,
                labelset_column_id=dataset.labelset_by_name(target_col).id,
                new_labelset_args=new_labelset_args,
                new_questionnaire_args=new_questionnaire_args,
                model_training_options=model_training_options,
                model_type=model_type,
            )
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

    def get_file_bytes(self, file_url: str) -> bytes:
        return self.get_storage_object(file_url)

    def get_img_bytes_from_etl_url(self, etl_url: str) -> List[bytes]:
        """
        Get image bytes for each page from workflow result etl output

        Args:
            etl_url (str): url from "etl_output" key of workflow result json

        Returns:
            image_bytes
        """
        image_bytes = []
        etl_response = self.get_storage_object(etl_url)
        for page in etl_response["pages"]:
            page_bytes = self.get_storage_object(page["image"])
            image_bytes.append(page_bytes)
        return image_bytes

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
        timeout: int = 180,
        return_raw_json: bool = False,
        raise_exception_for_failed: bool = False,
        return_failed_results: bool = True,
        ignore_deleted_submissions: bool = False,
    ) -> List[WorkflowResult]:
        """
        Wait for submission to pass through workflow models and get result. If Review is enabled,
        result may be retrieved prior to human review.

        Args:
            submission_ids (List[int]): Ids of submission predictions to retrieve
            timeout (int): seconds permitted for each submission prior to timing out
            return_raw_json: (bool) = If True return raw json result, otherwise return WorkflowResult object.
            raise_exception_for_failed (bool): if True, ToolkitStatusError raised for failed submissions
            return_failed_results (bool): if True, return objects for failed submissions
            ignore_deleted_submissions (bool): if True, ignore deleted submissions

        Returns:
            List[WorkflowResult]: workflow result objects
        """
        results = []
        self.wait_for_submissions_to_process(submission_ids, timeout)
        for subid in submission_ids:
            submission: Submission = self.get_submission_object(subid)
            if submission.status == "FAILED":
                message = f"FAILURE, Submission: {subid}. {submission.errors}"
                if raise_exception_for_failed:
                    raise ToolkitStatusError(message)
                elif not return_failed_results:
                    print(message)
                    continue
            if submission.deleted and ignore_deleted_submissions:
                continue
            result = self._create_result(submission)
            # Add path to original input file to result
            result["input_file"] = submission.input_file
            if return_raw_json:
                results.append(result)
            else:
                results.append(WorkflowResult(result))
        return results

    def _create_result(self, submission: Union[Submission, int]):
        """
        Assumes you already checked that the submission result is COMPLETE
        """
        job = self.client.call(SubmissionResult(submission, wait=True))
        return self.get_storage_object(job.result)

    def submit_submission_review(
        self, submission_id: int, updated_predictions: dict, wait: bool = True
    ):
        job = self.client.call(SubmitReview(submission_id, changes=updated_predictions))
        if wait:
            job = self.client.call(JobStatus(job.id, wait=True))
        return job

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

    def wait_for_submissions_to_process(
        self, submission_ids: List[int], timeout_seconds: int = 180
    ) -> None:
        """
        Wait for submissions to reach a terminal status of "COMPLETE", "PENDING_AUTO_REVIEW",
        "FAILED", or "PENDING_REVIEW"
        """
        self.client.call(WaitForSubmissions(submission_ids, timeout_seconds))

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
