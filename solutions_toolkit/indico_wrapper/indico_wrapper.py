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
    Submission
)

from indico import IndicoClient, IndicoConfig

# TODO: Need unittesting for this class
# Start with testing that kwargs adds to the config appropriately
class IndicoWrapper:
    """
    Class to handle all indico api calls
    """

    def __init__(
        self, host_url: str, api_token_path: str=None, api_token: str=None, **kwargs
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
        if self.api_token:
            self.config["api_token"] = self.api_token
            
        for arg, value in kwargs.items():
            self.config[arg] = value
            
        indico_config = IndicoConfig(**self.config)
        self.indico_client = IndicoClient(config=indico_config)

    def get_storage_object(self, storage_url):
        return self.indico_client.call(RetrieveStorageObject(storage_url))

    def submit_updated_review(self, submission, updated_predictions):
        return self.indico_client.call(
            SubmitReview(submission.id, changes=updated_predictions)
        )

    def graphQL_request(self, graphql_query, variables):
        return self.indico_client.call(
            GraphQLRequest(query=graphql_query, variables=variables)
        )

    def get_dataset(self, dataset_id):
        return self.indico_client.call(GetDataset(dataset_id))

    def create_export(self, dataset_id, **kwargs):
        return self.indico_client.call(
            CreateExport(dataset_id=dataset_id, **kwargs)
        )

    def download_export(self, export_id):
        return self.indico_client.call(DownloadExport(export_id))
