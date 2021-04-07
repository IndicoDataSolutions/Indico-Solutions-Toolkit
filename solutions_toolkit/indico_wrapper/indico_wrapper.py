from typing import List
from indico.queries import (
    RetrieveStorageObject,
    SubmissionFilter,
    ListSubmissions,
    SubmitReview,
    GetSubmission,
    WorkflowSubmission,
    WaitForSubmissions,
    SubmissionResult,
    UpdateSubmission,
    GraphQLRequest,
    GetDataset,
    CreateExport,
    DownloadExport,
    Submission,
)

from indico import IndicoClient, IndicoConfig

# TODO: Need unittesting for this class
# Start with testing that kwargs adds to the config appropriately
class IndicoWrapper:
    """
    Class to handle all indico api calls
    """

    def __init__(
        self, host_url: str, api_token_path: str = None, api_token: str = None, **kwargs
    ):
        """
        Create indico client with user provided arguments
        
        args:
            host (str): url of Indico environment
            api_token_path (str): local path to Indico API token
            api_token (str): Indico API token string
            
        """
        self.host_url = host_url
        self.api_token_path = api_token_path
        self.api_token = api_token

        self.config = {"host": self.host_url}

        if self.api_token_path:
            self.config["api_token_path"] = self.api_token_path

        elif self.api_token:
            self.config["api_token"] = self.api_token

        for arg, value in kwargs.items():
            self.config[arg] = value

        indico_config = IndicoConfig(**self.config)
        self.indico_client = IndicoClient(config=indico_config)

    def get_submission(self, submission_id: int) -> Submission:
        """
        Submission object query by submission id
        
        args:
            submission_id (str): id of submision to workflow
        
        returns:
            [Submission]: Indico Submission object
        """
        submission_obj = self.indico_client.call(GetSubmission(submission_id))
        return submission_obj

    def get_submissions_by_status(
        self,
        workflow_id: int,
        submission_status: str = "COMPLETE",
        retrieved_flag: bool = False,
    ) -> List[Submission]:
        """
        Get a list of submission objects from a given workflow and filter by
        submission status and retrieved flag
        
        workflow_id (int): id of workflow, can be found in the url of workflow page
        submission_status (str): status to query submissions by, only 3 are valid:
                                 COMPLETE, PENDING_REVIEW, PENDING_ADMIN_REVIEW, PENDING_AUTO_REVIEW
        retrieved_flag (bool): if True, return retrieved values, if False return unretrieved values
        
        returns: 
            List[Submission]: list of Submission objects
        """
        sub_filter = SubmissionFilter(
            status=submission_status, retrieved=retrieved_flag
        )
        complete_submissions = self.indico_client.call(
            ListSubmissions(workflow_ids=[workflow_id], filters=sub_filter)
        )
        return complete_submissions

    def get_workflow_output(self, submission):
        return self.indico_client.call(RetrieveStorageObject(submission.result_file))

    # TODO: make this more of a helper function and create specfic download functions
    # Ideally more functions like "get_submission_results" maybe "get_ocr_output?"
    def get_storage_object(self, storage_url):
        return self.indico_client.call(RetrieveStorageObject(storage_url))

    def get_submission_result(self, submission):
        sub_job = self.indico_client.call(SubmissionResult(submission.id, wait=True))
        result = self.get_storage_object(sub_job.result)
        return result

    def submit_updated_review(self, submission, updated_predictions):
        return self.indico_client.call(
            SubmitReview(submission.id, changes=updated_predictions)
        )

    def upload_to_workflow(self, workflow_id, pdf_filepaths):
        """
        Return a list of submission ids
        """
        return self.indico_client.call(
            WorkflowSubmission(workflow_id=workflow_id, files=pdf_filepaths)
        )

    def wait_for_submission(self, submission_ids, timeout=60):
        return self.indico_client.call(
            WaitForSubmissions(submission_ids=submission_ids, timeout=timeout)
        )

    def mark_retreived(self, submission):
        self.indico_client.call(UpdateSubmission(submission.id, retrieved=True))

    def graphQL_request(self, graphql_query, variables):
        return self.indico_client.call(
            GraphQLRequest(query=graphql_query, variables=variables)
        )

    def get_dataset(self, dataset_id):
        return self.indico_client.call(GetDataset(dataset_id))

    def create_export(self, dataset_id, **kwargs):
        return self.indico_client.call(CreateExport(dataset_id=dataset_id, **kwargs))

    def download_export(self, export_id):
        return self.indico_client.call(DownloadExport(export_id))
